import pyttsx3
import time

def generate_tts(text):
    engine = pyttsx3.init()
    tts_path = f"tts_{int(time.time())}.mp3"  # Unique file name
    engine.save_to_file(text, tts_path)
    engine.runAndWait()
    return tts_path