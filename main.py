import time
import os
from openwa import WhatsAPIDriver
from message_processing import process_text_message
from storage import load_json, save_json
from bot_config import BOT_NAME, MASTER_CONTACT_NAME, PAIRED_FILE, BANNED_FILE, MUTED_FILE, MESSAGE_LIMIT, LIMIT_RESET_SECONDS
from session_manager import start_all_sessions, clients, load_sessions

def main():
    # Initialize storage for message limits
    user_message_counts = {}

    # Initialize main session (master)
    main_profile_dir = os.path.abspath("profiles/main")
    os.makedirs(main_profile_dir, exist_ok=True)
    main_driver = WhatsAPIDriver(username="main", client='chrome', profile=main_profile_dir, headful=False)
    print("Waiting for main QR if not logged in...")
    main_driver.get_qr()  # Saves QR if needed
    main_driver.wait_for_login()

    # Start all paired sessions
    start_all_sessions()

    # Load banned and muted users (bot-wide)
    banned_users = load_json(BANNED_FILE)
    muted_users = load_json(MUTED_FILE)

    def message_limit_check(user):
        now = time.time()
        usage = user_message_counts.get(user, {"count": 0, "reset": now + LIMIT_RESET_SECONDS})
        if now > usage["reset"]:
            usage = {"count": 0, "reset": now + LIMIT_RESET_SECONDS}
        if usage["count"] >= MESSAGE_LIMIT and user != MASTER_CONTACT_NAME:
            main_driver.send_message_to_id(user, f"⏳ {user}, you have reached your message limit. Try again later.")
            return False
        usage["count"] += 1
        user_message_counts[user] = usage
        return True

    # Message observer for main session
    class MainMessageObserver:
        def on_message_received(self, new_messages):
            for message in new_messages:
                if message_limit_check(message.sender.id):
                    process_text_message(message.sender.id, message.content, main_driver, message.chat_id, None)

    main_driver.subscribe_new_messages(MainMessageObserver())

    # Keep the script running
    while True:
        time.sleep(1)  # Keep alive; adjust as needed

if __name__ == "__main__":
    main()