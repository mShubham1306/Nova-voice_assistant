"""
NOVA Configuration — Pydantic-Settings powered, .env-driven.
All values have sensible defaults so NOVA works out of the box.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    # ── Identity ──────────────────────────────────────────────────────────────
    ASSISTANT_NAME: str = "Nova"
    WAKE_WORD: str = "hey nova"

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    SECRET_KEY: str = "nova-super-secret-key-change-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

    # ── Voice Engine ──────────────────────────────────────────────────────────
    VOICE_RATE: int = 180
    VOICE_GENDER: str = "female"          # "male" | "female"
    LISTEN_TIMEOUT: int = 5
    PHRASE_TIME_LIMIT: int = 8
    LANGUAGE: str = "en-in"

    # ── AI / Gemini ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_TOKENS: int = 512

    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR: Path = BASE_DIR / "data"
    NOTES_DIR: Path = BASE_DIR / "data" / "notes"
    SCREENSHOTS_DIR: Path = BASE_DIR / "data" / "screenshots"
    MEMORY_FILE: Path = BASE_DIR / "data" / "memory.json"

    # ── User Environment (for developer workflows) ────────────────────────────
    USER_HOME: Path = Path.home()
    PROJECTS_DIR: Path = Field(default_factory=lambda: Path.home() / "Desktop")
    DOWNLOADS_DIR: Path = Field(default_factory=lambda: Path.home() / "Downloads")
    DOCUMENTS_DIR: Path = Field(default_factory=lambda: Path.home() / "Documents")

    # ── App Paths (Windows) ───────────────────────────────────────────────────
    APP_PATHS: dict[str, str] = {
        "chrome":         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "notepad":        "notepad.exe",
        "wordpad":        "wordpad.exe",
        "calculator":     "calc.exe",
        "paint":          "mspaint.exe",
        "word":           "winword.exe",
        "excel":          "excel.exe",
        "powerpoint":     "powerpnt.exe",
        "file explorer":  "explorer.exe",
        "explorer":       "explorer.exe",
        "cmd":            "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell":     "powershell.exe",
        "task manager":   "taskmgr.exe",
        "settings":       "ms-settings:",
        "control panel":  "control.exe",
        "snipping tool":  "snippingtool.exe",
        "vscode":         "code",
        "vs code":        "code",
        "visual studio code": "code",
        "spotify":        "spotify.exe",
        "discord":        "discord.exe",
        "telegram":       "telegram.exe",
        "whatsapp":       "whatsapp.exe",
        "vlc":            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        "postman":        "postman.exe",
        "git bash":       r"C:\Program Files\Git\git-bash.exe",
    }

    # ── Website Shortcuts ─────────────────────────────────────────────────────
    WEBSITE_SHORTCUTS: dict[str, str] = {
        "google":         "https://www.google.com",
        "youtube":        "https://www.youtube.com",
        "github":         "https://github.com",
        "gmail":          "https://mail.google.com",
        "google drive":   "https://drive.google.com",
        "google maps":    "https://maps.google.com",
        "twitter":        "https://twitter.com",
        "instagram":      "https://www.instagram.com",
        "facebook":       "https://www.facebook.com",
        "reddit":         "https://www.reddit.com",
        "linkedin":       "https://www.linkedin.com",
        "amazon":         "https://www.amazon.in",
        "netflix":        "https://www.netflix.com",
        "stackoverflow":  "https://stackoverflow.com",
        "chatgpt":        "https://chat.openai.com",
        "wikipedia":      "https://www.wikipedia.org",
        "localhost":      "http://localhost:3000",
    }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton settings instance
settings = Settings()
Config = settings  # Alias for backward compatibility

# Ensure data directories exist (with fallback for read-only serverless environments like Vercel/AWS Lambda)
is_serverless = bool(
    os.getenv("VERCEL")
    or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.path.exists("/var/task")
    or not os.access(str(BASE_DIR), os.W_OK)
)

if is_serverless:
    tmp_data = Path("/tmp/nova_data")
    settings.DATA_DIR = tmp_data
    settings.NOTES_DIR = tmp_data / "notes"
    settings.SCREENSHOTS_DIR = tmp_data / "screenshots"
    settings.MEMORY_FILE = tmp_data / "memory.json"

for _dir in [settings.DATA_DIR, settings.NOTES_DIR, settings.SCREENSHOTS_DIR]:
    try:
        _dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


