import uuid
import os
import shutil
import base64
from openwa import WhatsAPIDriver
from storage import load_json, save_json
from bot_config import BOT_NAME, MASTER_CONTACT_NAME
from message_processing import process_text_message

PAIRED_SESSIONS_FILE = "paired_sessions.json"
PROFILES_DIR = "profiles"

if not os.path.exists(PROFILES_DIR):
    os.makedirs(PROFILES_DIR)

clients = {}

def load_sessions():
    return load_json(PAIRED_SESSIONS_FILE, default={})

def save_sessions(sessions):
    save_json(PAIRED_SESSIONS_FILE, sessions)

def create_session(main_driver, requester_jid, number):
    sessions = load_sessions()
    session_id = str(uuid.uuid4())
    profile_dir = os.path.abspath(f"{PROFILES_DIR}/{session_id}")
    os.makedirs(profile_dir, exist_ok=True)
    driver = WhatsAPIDriver(username=session_id, client='chrome', profile=profile_dir, headful=False)
    clients[session_id] = driver

    # Get QR
    qr_base64 = driver.get_qr_base64()
    qr_path = f"qr_{session_id}.png"
    with open(qr_path, "wb") as f:
        f.write(base64.b64decode(qr_base64))
    main_driver.send_image_to_id(requester_jid, qr_path, "Scan this QR with your phone to link the account.")
    os.remove(qr_path)

    # Wait for login
    driver.wait_for_login()

    owner_jid = f"{number}@s.whatsapp.net"
    sessions[session_id] = {
        'owner_jid': owner_jid,
        'profile_dir': profile_dir,
        'active': True,
        'requester_jid': requester_jid
    }
    save_sessions(sessions)
    main_driver.send_message_to_id(requester_jid, f"Session linked successfully! The bot is now running on your number (Session ID: {session_id}). Use !bot on/off to control it.")

    # Subscribe to messages
    driver.subscribe_new_messages(MessageObserver(session_id))

    return session_id

class MessageObserver:
    def __init__(self, session_id):
        self.session_id = session_id

    def on_message_received(self, new_messages):
        for message in new_messages:
            # Apply message limit check in main.py, not here
            process_text_message(message.sender.id, message.content, clients[self.session_id], message.chat_id, self.session_id)

def delete_session(session_id):
    sessions = load_sessions()
    if session_id in sessions:
        if session_id in clients:
            clients[session_id].close()
            del clients[session_id]
        profile_dir = sessions[session_id]['profile_dir']
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir, ignore_errors=True)
        del sessions[session_id]
        save_sessions(sessions)

def toggle_session(session_id, active):
    sessions = load_sessions()
    if session_id in sessions:
        sessions[session_id]['active'] = active
        save_sessions(sessions)
        if active:
            profile_dir = sessions[session_id]['profile_dir']
            driver = WhatsAPIDriver(username=session_id, client='chrome', profile=profile_dir, headful=False)
            clients[session_id] = driver
            driver.wait_for_login()
            driver.subscribe_new_messages(MessageObserver(session_id))
        else:
            if session_id in clients:
                clients[session_id].close()
                del clients[session_id]

def start_all_sessions():
    sessions = load_sessions()
    for session_id, data in sessions.items():
        if data['active']:
            profile_dir = data['profile_dir']
            driver = WhatsAPIDriver(username=session_id, client='chrome', profile=profile_dir, headful=False)
            clients[session_id] = driver
            driver.wait_for_login()
            driver.subscribe_new_messages(MessageObserver(session_id))