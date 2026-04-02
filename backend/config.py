import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration for NOVA Voice Assistant."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "nova-secret-key-2024")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    # Voice Engine
    WAKE_WORD = "hey nova"
    ASSISTANT_NAME = "Nova"
    VOICE_RATE = int(os.getenv("VOICE_RATE", 180))
    VOICE_GENDER = os.getenv("VOICE_GENDER", "female")  # "male" or "female"
    LISTEN_TIMEOUT = int(os.getenv("LISTEN_TIMEOUT", 5))
    PHRASE_TIME_LIMIT = int(os.getenv("PHRASE_TIME_LIMIT", 8))
    LANGUAGE = os.getenv("LANGUAGE", "en-in")

    # Google Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Paths
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
    NOTES_DIR = os.path.join(os.path.dirname(__file__), "notes")

    # App shortcuts (Windows)
    APP_PATHS = {
        "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "file explorer": "explorer.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        "task manager": "taskmgr.exe",
        "settings": "ms-settings:",
        "control panel": "control.exe",
        "snipping tool": "snippingtool.exe",
        "vscode": "code",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "telegram": "telegram.exe",
        "whatsapp": "whatsapp.exe",
    }

    # Website shortcuts
    WEBSITE_SHORTCUTS = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "google drive": "https://drive.google.com",
        "google maps": "https://maps.google.com",
        "twitter": "https://twitter.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "reddit": "https://www.reddit.com",
        "linkedin": "https://www.linkedin.com",
        "amazon": "https://www.amazon.com",
        "netflix": "https://www.netflix.com",
        "stackoverflow": "https://stackoverflow.com",
        "chatgpt": "https://chat.openai.com",
        "wikipedia": "https://www.wikipedia.org",
    }
