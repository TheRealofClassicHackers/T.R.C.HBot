import random
import json

def get_random_quote(quotes_file):
    quotes = load_json(quotes_file)
    if not quotes:
        return "No quotes available."
    return random.choice(quotes)

def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []