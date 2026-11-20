import os
import sys
import re
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Auto-detect venv if current environment lacks dependencies
def _ensure_environment():
    try:
        import ollama
        import sounddevice
        import speech_recognition
        import edge_tts
        import soundfile
    except ImportError:
        venv_py = BASE_DIR / "venv" / "Scripts" / "python.exe"
        if venv_py.exists() and sys.executable.lower() != str(venv_py).lower():
            import subprocess
            res = subprocess.run([str(venv_py)] + sys.argv)
            sys.exit(res.returncode)

_ensure_environment()

from brain.llm import ask_ai, get_available_models
from personality.identity import get_identity, update_name
from memory.memory_manager import init_memory
from voice.speech_to_text import listen_and_transcribe
from voice.text_to_speech import speak_text, detect_language

def check_ollama() -> bool:
    """Check if Ollama service is reachable."""
    import urllib.request
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "MyAI"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

def print_banner(identity: dict, models: list):
    name = identity.get("name", "Assistant")
    avatar = identity.get("avatar", "✨")
    active_model = models[0] if models else "tinyllama"

    print("\033[95m" + "=" * 64)
    print(f"        {avatar}  MY AI - NATURAL VOICE COMPANION")
    print("=" * 64 + "\033[0m")
    print(f"  • Companion Name : \033[92m{name}\033[0m")
    print(f"  • Voice Quality  : \033[93mUltra-Natural Neural Voice (Jenny / Swara)\033[0m")
    print(f"  • Auto Language  : \033[96mAuto-Switches (English ⇄ Hindi ⇄ Hinglish)\033[0m")
    print(f"  • Flow           : \033[92mSpeaks First, Then Displays Text\033[0m")
    print("\033[95m" + "-" * 64 + "\033[0m")
    print("  \033[90mTip: Say \033[33m'switch to chat'\033[90m to type, or \033[33m'exit'\033[90m to stop.\033[0m")
    print("\033[95m" + "=" * 64 + "\033[0m\n")

def is_chat_switch_command(text: str) -> bool:
    t = text.lower().strip()
    return any(p in t for p in [
        "switch to chat", "chat mode", "text mode", "let's chat", "lets chat",
        "i want to chat", "type mode", "switch to text", "stop listening"
    ])

def is_voice_switch_command(text: str) -> bool:
    t = text.lower().strip()
    return any(p in t for p in [
        "switch to voice", "voice mode", "let's talk", "lets talk",
        "talk to me", "voice", "/v", "listen"
    ])

def is_exit_command(text: str) -> bool:
    t = text.lower().strip()
    return t in ["exit", "quit", "bye", "goodbye", "alvida", "/exit", "see you later"]

def run_desktop():
    init_memory()

    if not check_ollama():
        print("\033[91m⚠️ Ollama does not seem to be running on http://localhost:11434!\033[0m")
        print("  Please start it with: \033[93mollama serve\033[0m\n")

    identity = get_identity()
    models = get_available_models()
    print_banner(identity, models)

    chat_history = []
    mode = "voice"

    # Initial friendly greeting (Speaks first, then prints)
    greeting = "Hey! I'm here. What's on your mind?"
    speak_text(greeting)
    print(f"\033[95m{identity.get('name', 'Assistant')}\033[0m: {greeting}\n")

    while True:
        try:
            user_input = None

            if mode == "voice":
                print("\033[93m[🎙️ Listening...]\033[0m", end=" ", flush=True)
                spoken = listen_and_transcribe(duration=6.5)

                if not spoken or not spoken.strip():
                    continue

                user_input = spoken.strip()
                print(f"\r\033[94mYou\033[0m: {user_input}")

            else:
                print("\033[94mYou\033[0m: ", end="", flush=True)
                text_input = input().strip()
                if not text_input:
                    continue
                user_input = text_input

            # Detect language of user query
            user_lang = detect_language(user_input)

            # Check for Exit
            if is_exit_command(user_input):
                farewell = "अलविदा! फिर मिलेंगे।" if user_lang in ["hi", "hinglish"] else "Goodbye! Talk to you soon."
                speak_text(farewell, lang=user_lang)
                print(f"\n\033[95m{identity.get('name', 'Assistant')}\033[0m: {farewell}\n")
                break

            # Check for Switch to Chat
            if mode == "voice" and is_chat_switch_command(user_input):
                mode = "chat"
                ack = "जरूर! अब आप टाइप करके बात कर सकते हैं।" if user_lang in ["hi", "hinglish"] else "Sure thing! Switching to chat mode. Type whenever you're ready."
                speak_text(ack, lang=user_lang)
                print(f"\n\033[95m{identity.get('name', 'Assistant')}\033[0m: {ack}\n")
                continue

            # Check for Switch to Voice
            if mode == "chat" and is_voice_switch_command(user_input):
                mode = "voice"
                ack = "बहुत बढ़िया! मैं सुन रही हूँ।" if user_lang in ["hi", "hinglish"] else "Awesome! Switching to voice mode. I'm all ears!"
                speak_text(ack, lang=user_lang)
                print(f"\n\033[95m{identity.get('name', 'Assistant')}\033[0m: {ack}\n")
                continue

            # Check for Name Change
            lower_input = user_input.lower()
            if "your name is" in lower_input or "tumhara naam" in lower_input:
                words = user_input.strip().split()
                new_name = words[-1].strip(".,!?")
                reply = update_name(new_name)
                identity = get_identity()
                speak_text(reply, lang=user_lang)
                print(f"\n\033[95m{new_name}\033[0m: {reply}\n")
                continue

            # Generate response
            response = ask_ai(
                user_message=user_input,
                chat_history=chat_history,
                stream=False
            )

            # FIRST speak it aloud in natural human voice
            speak_text(response, lang=user_lang)

            # THEN display the text on screen
            print(f"\033[95m{identity.get('name', 'Assistant')}\033[0m: {response}\n")

            # Maintain conversation history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": response})
            if len(chat_history) > 6:
                chat_history = chat_history[-6:]

        except KeyboardInterrupt:
            print(f"\n\n\033[95m{identity.get('name', 'Assistant')}\033[0m: Catch you later!\n")
            break
        except Exception as e:
            print(f"\n\033[91m⚠️ Error: {e}\033[0m\n")

if __name__ == "__main__":
    run_desktop()