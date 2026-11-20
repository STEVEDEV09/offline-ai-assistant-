import os
import json
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VISION_DIR = BASE_DIR / "vision"
LOGS_DIR = BASE_DIR / "logs"

# Ensure essential directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# File Paths
IDENTITY_FILE = DATA_DIR / "identity.json"
CONFIG_FILE = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "memory.db"
AUDIT_LOG_FILE = LOGS_DIR / "audit_log.json"

# Vision Cascade Paths
FACE_CASCADE_PATH = VISION_DIR / "haarcascade_frontalface_default.xml"
SMILE_CASCADE_PATH = VISION_DIR / "haarcascade_smile.xml"
EYE_CASCADE_PATH = VISION_DIR / "haarcascade_eye.xml"

# Ollama / LLM Defaults
DEFAULT_MODEL = "tinyllama"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# UI Defaults
APP_TITLE = "JARVIS AI - Futuristic Desktop Companion"
APP_ICON = "⚡"

# Default Configuration
DEFAULT_CONFIG = {
    # AI Provider Settings
    "ai_provider": "ollama",  # "ollama", "openai", "gemini", "groq", "anthropic"
    "active_model": "tinyllama",
    "providers": {
        "ollama": {
            "host": OLLAMA_HOST,
            "default_model": "tinyllama"
        },
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o-mini"
        },
        "gemini": {
            "api_key_env": "GEMINI_API_KEY",
            "default_model": "gemini-1.5-flash"
        },
        "groq": {
            "api_key_env": "GROQ_API_KEY",
            "default_model": "llama-3.3-70b-versatile"
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "default_model": "claude-3-5-haiku-20241022"
        }
    },

    # Voice Engine Settings
    "voice": {
        "wake_word": "jarvis",
        "wake_word_enabled": True,
        "input_mode": "push_to_talk",  # "push_to_talk", "continuous", "manual"
        "preferred_language": "auto",  # "auto", "en", "hi", "hinglish", "te"
        "tts_provider": "edge",        # "edge", "sapi" (offline)
        "voice_rate": "+0%",
        "voice_pitch": "+0Hz",
        "voice_volume": 1.0,
        "silence_timeout": 1.2,
        "energy_threshold": 280.0,
        "audio_feedback": True,
        "auto_speak_replies": True,
        "voice_profiles": {
            "en": "en-US-JennyNeural",       # Siri-like warm conversational English
            "hi": "hi-IN-SwaraNeural",       # Natural Hindi
            "hinglish": "en-IN-NeerjaNeural",# Conversational Indian English/Hinglish
            "te": "te-IN-ShrutiNeural"       # Natural Telugu
        }
    },

    # System & Safety Policies
    "safety": {
        "require_confirmation_for_destructive": True,
        "require_confirmation_for_system_power": True,
        "require_confirmation_for_code_execution": True,
        "approved_directories": [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Documents"),
            str(BASE_DIR)
        ],
        "recycle_bin_deletion": True,  # Send to recycle bin instead of permanent delete
        "allow_web_browsing": True
    },

    # Application Launcher Aliases
    "app_aliases": {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "edge": "msedge.exe",
        "ms edge": "msedge.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "code": "code",
        "vs code": "code",
        "vscode": "code",
        "file manager": "explorer.exe",
        "explorer": "explorer.exe",
        "terminal": "wt.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "task manager": "taskmgr.exe",
        "paint": "mspaint.exe",
        "settings": "ms-settings:"
    },

    # Windows Notification Settings
    "notifications": {
        "speak_notifications": False,
        "privacy_mode": False,
        "poll_interval_seconds": 10,
        "muted_apps": []
    },

    # UI Theme & Appearance
    "ui": {
        "theme": "dark_futuristic",  # "dark_futuristic", "dark_minimal", "light"
        "accent_color": "#00f0ff",   # Electric Cyan
        "secondary_accent": "#0077ff", # Electric Blue
        "font_family": "Segoe UI",
        "minimize_to_tray": True,
        "orb_animation": True,
        "sound_effects": True
    }
}

def load_config() -> dict:
    """Load configuration from file, populating missing keys with defaults."""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)

        # Deep merge with defaults
        def merge_dicts(base: dict, user: dict) -> dict:
            merged = base.copy()
            for k, v in user.items():
                if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                    merged[k] = merge_dicts(merged[k], v)
                else:
                    merged[k] = v
            return merged

        return merge_dicts(DEFAULT_CONFIG, user_config)
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data: dict) -> None:
    """Safely write configuration to disk."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save config: {e}")

def get_setting(key_path: str, default=None):
    """Retrieve setting by dotted key path (e.g. 'voice.wake_word')."""
    cfg = load_config()
    keys = key_path.split(".")
    curr = cfg
    for k in keys:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        else:
            return default
    return curr

def update_setting(key_path: str, value) -> None:
    """Update setting by dotted key path and persist."""
    cfg = load_config()
    keys = key_path.split(".")
    curr = cfg
    for k in keys[:-1]:
        if k not in curr or not isinstance(curr[k], dict):
            curr[k] = {}
        curr = curr[k]
    curr[keys[-1]] = value
    save_config(cfg)
