import json
import os
from config.settings import IDENTITY_FILE

DEFAULT_IDENTITY = {
    "name": "Assistant",
    "user_name": "Friend",
    "avatar": "🤖",
    "personality": "I am a helpful, friendly, witty, and smart AI assistant running locally.",
    "system_instructions": "Keep answers clear, helpful, and concise. Be conversational and approachable."
}

def get_identity() -> dict:
    """Retrieve current identity dictionary, creating default if file doesn't exist."""
    if os.path.exists(IDENTITY_FILE):
        try:
            with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Fill any missing keys from defaults
                for k, v in DEFAULT_IDENTITY.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return DEFAULT_IDENTITY.copy()
    else:
        save_identity(DEFAULT_IDENTITY)
        return DEFAULT_IDENTITY.copy()

def save_identity(data: dict) -> None:
    """Save identity to JSON file safely."""
    os.makedirs(os.path.dirname(IDENTITY_FILE), exist_ok=True)
    with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_name(new_name: str) -> str:
    """Update AI name."""
    clean_name = new_name.strip()
    if not clean_name:
        return "Name cannot be empty."
    identity = get_identity()
    identity["name"] = clean_name
    save_identity(identity)
    return f"My name has been updated to {clean_name}!"

def update_user_name(new_user_name: str) -> str:
    """Update user's preferred name."""
    clean_name = new_user_name.strip()
    if not clean_name:
        return "User name cannot be empty."
    identity = get_identity()
    identity["user_name"] = clean_name
    save_identity(identity)
    return f"Nice to meet you, {clean_name}! I will remember your name."

def update_personality(new_personality: str) -> str:
    """Update AI personality prompt."""
    identity = get_identity()
    identity["personality"] = new_personality.strip()
    save_identity(identity)
    return "Personality updated successfully!"

def reset_identity() -> dict:
    """Reset identity back to default."""
    save_identity(DEFAULT_IDENTITY)
    return DEFAULT_IDENTITY.copy()