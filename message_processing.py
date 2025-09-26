import random
import time
import threading
import json
import uuid
import os
from media_downloader import (
    download_tiktok_video, search_youtube_video,
    download_youtube_video, convert_video_to_mp3
)
from anime_scraper import download_anime_episode
from bot_config import BOT_NAME, MASTER_CONTACT_NAME
from storage import load_json, save_json
from poll_manager import create_poll, vote_in_poll, get_poll_results
from reminder_manager import set_reminder
from quote_manager import get_random_quote
from tts_manager import generate_tts
from meme_generator import generate_meme
from translate_manager import translate_to_pig_latin
from funfont_converter import convert_to_funfont
from gif_downloader import download_gif
from session_manager import clients, load_sessions, create_session, delete_session, toggle_session

PREFIX = "!"
LOGO_PATH = os.environ.get("LOGO_PATH", "/app/bot_logo.png")  # Railway path
CREDITS = "Powered by YourName 🚀"

# File paths
PAIRED_FILE = "paired_users.json"
BANNED_FILE = "banned_users.json"
MUTED_FILE = "muted_users.json"
POLLS_FILE = "polls.json"
REMINDERS_FILE = "reminders.json"
QUOTES_FILE = "quotes.json"

# Load data
banned_users = load_json(BANNED_FILE)
muted_users = load_json(MUTED_FILE)
polls = load_json(POLLS_FILE)
reminders = load_json(REMINDERS_FILE)

# Bot configuration
IS_PREMIUM = os.environ.get("IS_PREMIUM", "False") == "True"
BOT_VERSION = "1.3"
BOT_START_TIME = time.time()

def format_message(text):
    """Wrap text in ASCII box with arrows and emojis."""
    lines = text.split("\n")
    max_len = max(len(line) for line in lines)
    box_top = f"🟢 {'═' * (max_len + 2)} 🟢"
    box_bottom = f"🔴 {'═' * (max_len + 2)} 🔴"
    formatted = [box_top]
    for line in lines:
        formatted.append(f"➡️ {line.ljust(max_len)} ⬅️")
    formatted.append(box_bottom)
    formatted.append(CREDITS)
    return "\n".join(formatted)

def send_formatted_message(whatsapp_client, chat_id, text):
    """Send text message with logo and formatted box."""
    if os.path.exists(LOGO_PATH):
        whatsapp_client.send_image_to_id(chat_id, LOGO_PATH, format_message(text))
    else:
        whatsapp_client.send_message_to_id(chat_id, format_message(text))

def process_text_message(user, text, whatsapp_client, chat_id, session_id=None):
    is_group = chat_id.endswith('@g.us')
    sessions = load_sessions()
    is_owner = session_id and user == sessions.get(session_id, {}).get('owner_jid', '')
    is_master = user == MASTER_CONTACT_NAME

    if session_id and not sessions.get(session_id, {}).get('active', False):
        if not is_owner and not is_master:
            return

    text = text.strip()
    if not text.startswith(PREFIX):
        if polls:
            for poll_id, poll in polls.items():
                if poll["active"] and text.strip().isdigit():
                    vote = int(text.strip())
                    if 1 <= vote <= len(poll["options"]):
                        vote_in_poll(poll_id, user, vote, POLLS_FILE)
                        whatsapp_client.send_image_to_id(chat_id, LOGO_PATH, f"✅ Vote recorded for '{poll['question']}'!\n\n{CREDITS}")
                        return
        return

    command_text = text[len(PREFIX):].strip().lower()

    if user in banned_users:
        send_formatted_message(whatsapp_client, chat_id, "🚫 You are banned and cannot use the bot.")
        return

    if user in muted_users:
        send_formatted_message(whatsapp_client, chat_id, "🔇 You are muted and cannot send commands.")
        return

    if is_master or is_owner:
        if command_text == "help":
            send_formatted_message(whatsapp_client, chat_id, 
                f"Commands:\n"
                f"{PREFIX}pair <number> (master only, private), {PREFIX}help, {PREFIX}tiktok <url>, {PREFIX}songdl <song name>, {PREFIX}animedl <anime name>\n"
                f"{PREFIX}flirt, {PREFIX}roast, {PREFIX}translate <text>, {PREFIX}funfont <text>, {PREFIX}tts <text>\n"
                f"{PREFIX}meme <top text> | <bottom text>, {PREFIX}ban <user>, {PREFIX}unban <user>, {PREFIX}mute <user>, {PREFIX}unmute <user>\n"
                f"{PREFIX}grouprules <text>, {PREFIX}poll <question> | <option1> | <option2> | ..., {PREFIX}pollresults <poll_id>\n"
                f"{PREFIX}remind <time> <message>, {PREFIX}quote, {PREFIX}roll <sides>, {PREFIX}info, {PREFIX}echo <text>\n"
                f"{PREFIX}session, {PREFIX}promote <user>, {PREFIX}demote <user>, {PREFIX}kick <user>, {PREFIX}add <user>\n"
                f"{PREFIX}gif <url>, {PREFIX}bot on, {PREFIX}bot off (owner only), {PREFIX}del session <id> (master only, private)"
            )
            return

        if command_text.startswith("ban "):
            target = command_text[4:].strip()
            banned_users.add(target)
            save_json(BANNED_FILE, banned_users)
            send_formatted_message(whatsapp_client, chat_id, f"🚫 User {target} banned from bot usage.")
            return

        if command_text.startswith("unban "):
            target = command_text[6:].strip()
            banned_users.discard(target)
            save_json(BANNED_FILE, banned_users)
            send_formatted_message(whatsapp_client, chat_id, f"✅ User {target} unbanned from bot usage.")
            return

        if command_text.startswith("mute "):
            target = command_text[5:].strip()
            muted_users.add(target)
            save_json(MUTED_FILE, muted_users)
            send_formatted_message(whatsapp_client, chat_id, f"🔇 User {target} muted.")
            return

        if command_text.startswith("unmute "):
            target = command_text[7:].strip()
            muted_users.discard(target)
            save_json(MUTED_FILE, muted_users)
            send_formatted_message(whatsapp_client, chat_id, f"✅ User {target} unmuted.")
            return

        if command_text.startswith("grouprules "):
            rules_text = text[len(PREFIX)+11:].strip()
            send_formatted_message(whatsapp_client, chat_id, f"Group rules updated to:\n{rules_text}")
            return

        if command_text.startswith("poll "):
            parts = text[len(PREFIX)+5:].strip().split("|")
            if len(parts) < 3:
                send_formatted_message(whatsapp_client, chat_id, "❌ Poll format: !poll <question> | <option1> | <option2> | ...")
                return
            question = parts[0].strip()
            options = [opt.strip() for opt in parts[1:]]
            poll_id = create_poll(question, options, POLLS_FILE)
            send_formatted_message(whatsapp_client, chat_id, 
                f"📊 Poll created (ID: {poll_id})\nQuestion: {question}\n" +
                "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)]) +
                "\nReply with a number to vote!"
            )
            return

        if command_text.startswith("pollresults "):
            poll_id = command_text[12:].strip()
            results = get_poll_results(poll_id, POLLS_FILE)
            send_formatted_message(whatsapp_client, chat_id, results)
            return

        if not is_group:
            if command_text.startswith(("promote ", "demote ", "kick ", "add ")):
                send_formatted_message(whatsapp_client, chat_id, "❌ This command is only available in group chats.")
                return

        if command_text.startswith("promote "):
            target = command_text[8:].strip()
            try:
                group_chat = whatsapp_client.get_chat_from_id(chat_id)
                group_chat.promote_participant_admin_group(target)
                send_formatted_message(whatsapp_client, chat_id, f"👑 User {target} promoted to admin in this group.")
            except Exception as e:
                send_formatted_message(whatsapp_client, chat_id, f"Error promoting user: {e}")
            return

        if command_text.startswith("demote "):
            target = command_text[7:].strip()
            try:
                group_chat = whatsapp_client.get_chat_from_id(chat_id)
                group_chat.demote_participant_admin_group(target)
                send_formatted_message(whatsapp_client, chat_id, f"⬇️ User {target} demoted from admin in this group.")
            except Exception as e:
                send_formatted_message(whatsapp_client, chat_id, f"Error demoting user: {e}")
            return

        if command_text.startswith("kick "):
            target = command_text[5:].strip()
            try:
                group_chat = whatsapp_client.get_chat_from_id(chat_id)
                group_chat.remove_participant_group(target)
                send_formatted_message(whatsapp_client, chat_id, f"🚪 User {target} kicked from this group.")
            except Exception as e:
                send_formatted_message(whatsapp_client, chat_id, f"Error kicking user: {e}")
            return

        if command_text.startswith("add "):
            target = command_text[4:].strip()
            try:
                group_chat = whatsapp_client.get_chat_from_id(chat_id)
                group_chat.add_participant_group(target)
                send_formatted_message(whatsapp_client, chat_id, f"➕ User {target} added to this group.")
            except Exception as e:
                send_formatted_message(whatsapp_client, chat_id, f"Error adding user: {e}")
            return

        if command_text == "bot on":
            if session_id and (is_owner or is_master):
                toggle_session(session_id, True)
                send_formatted_message(whatsapp_client, chat_id, "⏯️ Bot activated for this session.")
            return

        if command_text == "bot off":
            if session_id and (is_owner or is_master):
                toggle_session(session_id, False)
                send_formatted_message(whatsapp_client, chat_id, "⏯️ Bot deactivated for this session.")
            return

    if session_id is None and is_master and not is_group:
        if command_text.startswith("pair "):
            number = command_text[5:].strip()
            create_session(whatsapp_client, user, number)
            send_formatted_message(whatsapp_client, chat_id, f"Pairing started for {number}. QR sent.")
            return

        if command_text.startswith("del session "):
            target_session = command_text[12:].strip()
            delete_session(target_session)
            send_formatted_message(whatsapp_client, chat_id, "Deleting user's session. This is a private command for master.")
            return

    if command_text == "flirt":
        msgs = [
            "😘 Are you French? Because Eiffel for you.",
            "😍 I got lost in your eyes.",
            "📶 Are you Wi-Fi? Because I'm connected to you."
        ]
        send_formatted_message(whatsapp_client, chat_id, random.choice(msgs))
        return

    if command_text == "roast":
        msgs = [
            "☁️ You're like a cloud.",
            "🤡 As useless as the 'ueue' in 'queue'.",
            "🎉 You ruin every party you enter."
        ]
        send_formatted_message(whatsapp_client, chat_id, random.choice(msgs))
        return

    if command_text.startswith("translate "):
        to_translate = text[len(PREFIX)+10:].strip()
        result = translate_to_pig_latin(to_translate)
        send_formatted_message(whatsapp_client, chat_id, f"Pig Latin: {result}")
        return

    if command_text.startswith("funfont "):
        to_convert = text[len(PREFIX)+8:].strip()
        fun_text = convert_to_funfont(to_convert)
        send_formatted_message(whatsapp_client, chat_id, fun_text)
        return

    if command_text.startswith("tts "):
        to_speak = text[len(PREFIX)+4:].strip()
        try:
            tts_path = generate_tts(to_speak)
            whatsapp_client.send_media_to_id(chat_id, tts_path, f"Voice message\n\n{CREDITS}")
        except Exception as e:
            send_formatted_message(whatsapp_client, chat_id, f"Error generating TTS: {e}")
        return

    if command_text.startswith("meme "):
        parts = text[len(PREFIX)+5:].strip().split("|")
        if len(parts) < 2:
            send_formatted_message(whatsapp_client, chat_id, "❌ Meme format: !meme <top text> | <bottom text>")
            return
        top_text = parts[0].strip()
        bottom_text = parts[1].strip()
        try:
            meme_path = generate_meme(top_text, bottom_text)
            whatsapp_client.send_image_to_id(chat_id, meme_path, f"Meme\n\n{CREDITS}")
        except Exception as e:
            send_formatted_message(whatsapp_client, chat_id, f"Error generating meme: {e}")
        return

    if command_text.startswith("tiktok "):
        url = command_text[7:].strip()
        send_formatted_message(whatsapp_client, chat_id, "Downloading TikTok video, please wait...")
        try:
            video_path = download_tiktok_video(url)
            whatsapp_client.send_video_to_id(chat_id, video_path, f"TikTok video\n\n{CREDITS}")
        except Exception as e:
            send_formatted_message(whatsapp_client, chat_id, f"Error downloading TikTok video: {e}")
        return

    if command_text.startswith("songdl "):
        song_name = command_text[7:].strip()
        send_formatted_message(whatsapp_client, chat_id, f"Searching song '{song_name}' on YouTube...")
        try:
            yt_url = search_youtube_video(song_name)
            if not yt_url:
                send_formatted_message(whatsapp_client, chat_id, "Song not found!")
                return
            video_path = download_youtube_video(yt_url)
            mp3_path = convert_video_to_mp3(video_path)
            send_formatted_message(whatsapp_client, chat_id, f"Sending you the song: {song_name}")
            whatsapp_client.send_media_to_id(chat_id, mp3_path, f"{song_name}\n\n{CREDITS}")
        except Exception as e:
            send_formatted_message(whatsapp_client, chat_id, f"Error downloading song: {e}")
        return

    if command_text.startswith("animedl "):
        anime_name = command_text[8:].strip()
        send_formatted_message(whatsapp_client, chat_id, f"Searching and downloading latest episode of '{anime_name}'...")
        try:
            file_or_url = download_anime_episode(anime_name)
            if file_or_url.endswith(".mp4"):
                whatsapp_client.send_media_to_id(chat_id, file_or_url, f"Anime episode\n\n{CREDITS}")
            else:
                send_formatted_message(whatsapp_client, chat_id, f"Video URL: {file_or_url}\nPlease open manually.")
        except Exception as e:
            send_formatted_message(whatsapp_client, chat_id, f"Failed to download anime: {e}")
        return

    if command_text.startswith("remind "):
        parts = text[len(PREFIX)+7:].strip().split(" ", 1)
        if len(parts) < 2:
            send_formatted_message(whatsapp_client, chat_id, "❌ Format: !remind <time> <message> (e.g., !remind 10m Study)")
            return
        time_str, message = parts
        try:
            set_reminder(user, time_str, message, REMINDERS_FILE, whatsapp_client)
            send_formatted_message(whatsapp_client, chat_id, f"⏰ Reminder set for {time_str}: {message}")
        except ValueError as e:
            send_formatted_message(whatsapp_client, chat_id, f"❌ Invalid time format: {e}")
        return

    if command_text == "quote":
        quote = get_random_quote(QUOTES_FILE)
        send_formatted_message(whatsapp_client, chat_id, f"💬 {quote}")
        return

    if command_text.startswith("roll "):
        sides = command_text[5:].strip()
        try:
            sides = int(sides)
            if sides < 1:
                raise ValueError
            result = random.randint(1, sides)
            send_formatted_message(whatsapp_client, chat_id, f"🎲 Rolled a {result} on a {sides}-sided die!")
        except ValueError:
            send_formatted_message(whatsapp_client, chat_id, "❌ Please provide a valid number of sides (e.g., !roll 6)")
        return

    if command_text == "info":
        uptime = int(time.time() - BOT_START_TIME)
        uptime_str = f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s"
        bot_type = "Premium" if IS_PREMIUM else "Free"
        send_formatted_message(whatsapp_client, chat_id, 
            f"🤖 {BOT_NAME} Info\n"
            f"Version: {BOT_VERSION}\n"
            f"Type: {bot_type}\n"
            f"Uptime: {uptime_str}\n"
            f"Master: {MASTER_CONTACT_NAME}\n"
            f"Commands: Type {PREFIX}help for a list\n"
            f"Session: {'Group' if is_group else 'Private'} chat ({chat_id})"
        )
        return

    if command_text == "session":
        session_type = "Group" if is_group else "Private"
        send_formatted_message(whatsapp_client, chat_id, f"📱 This is a {session_type} chat session (ID: {chat_id}).")
        return

    if command_text.startswith("echo "):
        echo_text = text[len(PREFIX)+5:].strip()
        send_formatted_message(whatsapp_client, chat_id, f"🗣️ {echo_text}")
        return

    if command_text.startswith("gif "):
        url = command_text[4:].strip()
        send_formatted_message(whatsapp_client, chat_id, "Downloading GIF, please wait...")
        try:
            gif_path = download_gif(url)
            whatsapp_client.send_video_as_gif_to_id(chat_id, gif_path, f"GIF\n\n{CREDITS}")
        except Exception as e:
            send_formatted_message(whatsapp_client, chat_id, f"Error downloading GIF: {e}")
        return

    send_formatted_message(whatsapp_client, chat_id, 
        f"❓ Unknown command. Type '{PREFIX}help' for list of commands.")