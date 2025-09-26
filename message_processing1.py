import random
from media_downloader import (
    download_tiktok_video, search_youtube_video,
    download_youtube_video, convert_video_to_mp3
)
from anime_scraper import download_anime_episode
from bot_config import BOT_NAME, MASTER_CONTACT_NAME
from storage import load_json, save_json
from bot_config import PAIRED_FILE, BANNED_FILE, MUTED_FILE

PREFIX = "!"

paired_users = load_json(PAIRED_FILE)
banned_users = load_json(BANNED_FILE)
muted_users = load_json(MUTED_FILE)

# Example helper functions for commands like translate, meme generation, tts, funfont...
def translate_command(command_text):
    # Your translation logic here
    return "Translated text (placeholder)"

def generate_meme():
    # Return a path or URL to a generated meme (placeholder)
    return "path/to/generated_meme.jpg"

def tts_command(text):
    # Return path to TTS audio file (placeholder)
    return "path/to/tts_audio.mp3"

def funfont_command(text):
    # Return fun font converted text (placeholder)
    return "𝓕𝓾𝓷 𝓣𝓮𝔁𝓽"

def process_text_message(user, text, whatsapp_client):
    text = text.strip()
    if not text.startswith(PREFIX):
        # Ignore or handle non-command messages here if desired
        return
    
    command_text = text[len(PREFIX):].strip().lower()

    if user in banned_users:
        whatsapp_client.send_message("🚫 You are banned and cannot use the bot.")
        return
    
    if user in muted_users:
        whatsapp_client.send_message("🔇 You are muted and cannot send commands.")
        return

    if user not in paired_users and user != MASTER_CONTACT_NAME:
        if command_text == "pair":
            paired_users.add(user)
            save_json(PAIRED_FILE, paired_users)
            whatsapp_client.send_message("🎉 You have successfully paired with the bot!")
        else:
            whatsapp_client.send_message(f"🔒 Please pair first by sending '{PREFIX}pair'.")
        return

    # Master commands
    if user == MASTER_CONTACT_NAME:
        if command_text == "help":
            whatsapp_client.send_message(
                f"Commands:\n"
                f"{PREFIX}pair, {PREFIX}help, {PREFIX}tiktok <url>, {PREFIX}songdl <song name>, {PREFIX}animedl <anime name>\n"
                f"{PREFIX}flirt, {PREFIX}roast, {PREFIX}translate <text>, {PREFIX}funfont <text>, {PREFIX}tts <text>\n"
                f"{PREFIX}meme, {PREFIX}ban <user>, {PREFIX}unban <user>, {PREFIX}mute <user>, {PREFIX}unmute <user>\n"
                f"{PREFIX}grouprules <text> (set group rules)\n"
            )
            return

        if command_text.startswith("ban "):
            target = command_text[4:].strip()
            banned_users.add(target)
            save_json(BANNED_FILE, banned_users)
            whatsapp_client.send_message(f"🚫 User {target} banned.")
            return

        if command_text.startswith("unban "):
            target = command_text[6:].strip()
            banned_users.discard(target)
            save_json(BANNED_FILE, banned_users)
            whatsapp_client.send_message(f"✅ User {target} unbanned.")
            return

        if command_text.startswith("mute "):
            target = command_text[5:].strip()
            muted_users.add(target)
            save_json(MUTED_FILE, muted_users)
            whatsapp_client.send_message(f"🔇 User {target} muted.")
            return

        if command_text.startswith("unmute "):
            target = command_text[7:].strip()
            muted_users.discard(target)
            save_json(MUTED_FILE, muted_users)
            whatsapp_client.send_message(f"✅ User {target} unmuted.")
            return

        if command_text.startswith("grouprules "):
            # Save group rules (implement your group rules saving logic)
            rules_text = text[len(PREFIX)+11:].strip()
            whatsapp_client.send_message(f"Group rules updated to:\n{rules_text}")
            return

    # Fun commands
    if command_text == "flirt":
        msgs = [
            "😘 Are you French? Because Eiffel for you.",
            "😍 I got lost in your eyes.",
            "📶 Are you Wi-Fi? Because I'm connected to you."
        ]
        whatsapp_client.send_message(random.choice(msgs))
        return

    if command_text == "roast":
        msgs = [
            "☁️ You're like a cloud.",
            "🤡 As useless as the 'ueue' in 'queue'.",
            "🎉 You ruin every party you enter."
        ]
        whatsapp_client.send_message(random.choice(msgs))
        return

    if command_text.startswith("translate "):
        to_translate = text[len(PREFIX)+9:].strip()
        result = translate_command(to_translate)
        whatsapp_client.send_message(result)
        return

    if command_text.startswith("funfont "):
        to_convert = text[len(PREFIX)+7:].strip()
        fun_text = funfont_command(to_convert)
        whatsapp_client.send_message(fun_text)
        return

    if command_text.startswith("tts "):
        to_speak = text[len(PREFIX)+3:].strip()
        tts_path = tts_command(to_speak)
        whatsapp_client.send_file(tts_path)
        return

    if command_text == "meme":
        meme_path = generate_meme()
        whatsapp_client.send_file(meme_path)
        return

    # TikTok download
    if command_text.startswith("tiktok "):
        url = command_text[7:].strip()
        whatsapp_client.send_message("Downloading TikTok video, please wait...")
        try:
            video_path = download_tiktok_video(url)
            whatsapp_client.send_video(video_path)
        except Exception as e:
            whatsapp_client.send_message(f"Error downloading TikTok video: {e}")
        return

    # YouTube song download with mp3 conversion
    if command_text.startswith("songdl "):
        song_name = command_text[7:].strip()
        whatsapp_client.send_message(f"Searching song '{song_name}' on YouTube...")
        try:
            yt_url = search_youtube_video(song_name)
            if not yt_url:
                whatsapp_client.send_message("Song not found!")
                return
            video_path = download_youtube_video(yt_url)
            mp3_path = convert_video_to_mp3(video_path)
            whatsapp_client.send_message(f"Sending you the song: {song_name}")
            whatsapp_client.send_file(mp3_path)
        except Exception as e:
            whatsapp_client.send_message(f"Error downloading song: {e}")
        return

    # Anime download
    if command_text.startswith("animedl "):
        anime_name = command_text[8:].strip()
        whatsapp_client.send_message(f"Searching and downloading latest episode of '{anime_name}'...")
        try:
            file_or_url = download_anime_episode(anime_name)
            if file_or_url.endswith(".mp4"):
                whatsapp_client.send_file(file_or_url)
            else:
                whatsapp_client.send_message(f"Video URL: {file_or_url}\nPlease open manually.")
        except Exception as e:
            whatsapp_client.send_message(f"Failed to download anime: {e}")
        return

    # Unknown command response
    whatsapp_client.send_message(
        f"❓ Unknown command. Type '{PREFIX}pair' to start or '{PREFIX}help' for list of commands."
    )
