import threading
import time
import re
import json

def parse_time(time_str):
    """Parse time string like '10m', '2h', '30s' into seconds."""
    match = re.match(r"(\d+)([smh])", time_str.lower())
    if not match:
        raise ValueError("Use format like 10m, 2h, or 30s")
    value, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600

def set_reminder(user, time_str, message, reminders_file, whatsapp_client):
    seconds = parse_time(time_str)
    reminders = load_json(reminders_file)
    reminder_id = str(int(time.time()))
    reminders[reminder_id] = {
        "user": user,
        "message": message,
        "trigger_time": int(time.time()) + seconds
    }
    save_json(reminders_file, reminders)
    
    def send_reminder():
        time.sleep(seconds)
        whatsapp_client.send_message(f"⏰ Reminder for {user}: {message}")
        reminders = load_json(reminders_file)
        reminders.pop(reminder_id, None)
        save_json(reminders_file, reminders)
    
    threading.Thread(target=send_reminder, daemon=True).start()

def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)