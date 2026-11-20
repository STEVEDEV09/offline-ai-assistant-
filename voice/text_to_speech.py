import asyncio
import io
import re
import threading
import soundfile as sf
import sounddevice as sd
import edge_tts

# Most natural, human-like neural voices (warm, conversational, zero robotic artifacts)
VOICE_MAP = {
    "en": "en-US-JennyNeural",   # Ultra-natural conversational Siri-like female
    "hi": "hi-IN-SwaraNeural",   # Expressive, natural Hindi female
    "hinglish": "en-IN-NeerjaNeural", # Sweet Indian English / Hinglish female
    "es": "es-ES-ElviraNeural",   # Natural Spanish female
    "fr": "fr-FR-DeniseNeural",   # Natural French female
    "ja": "ja-JP-NanamiNeural",   # Natural Japanese female
    "de": "de-DE-KatjaNeural",    # Natural German female
}

def detect_language(text: str) -> str:
    """Detect language of text for optimal voice selection."""
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"

    hindi_keywords = [
        "kya", "kaise", "kaisa", "kaisi", "hai", "hain", "haan", "nahi", "nahin",
        "batao", "aap", "tum", "mujhe", "mera", "meri", "namaste", "theek",
        "accha", "achha", "kholo", "samjhao", "bolo", "sunao", "karna", "chahiye",
        "dost", "shukriya", "dhanyawad", "kaun", "kaha", "kahan", "kab", "kyu", "kyun",
        "pucho", "bataiye", "samajh", "aaya"
    ]
    words = set(re.findall(r"\b\w+\b", text.lower()))
    if any(k in words for k in hindi_keywords):
        return "hinglish"

    # Spanish
    if any(k in words for k in ["hola", "gracias", "amigo", "buenos", "como"]):
        return "es"
    # French
    if any(k in words for k in ["bonjour", "salut", "merci", "comment"]):
        return "fr"

    return "en"

def clean_text_for_speech(text: str) -> str:
    """Strip code blocks, URLs, markdown formatting, and meta-tokens."""
    # Remove prefix artifacts like 'Assistant:' or 'User:'
    t = re.sub(r"^(?:Assistant|AI|User):\s*", "", text, flags=re.IGNORECASE)
    # Remove code blocks and inline code
    t = re.sub(r"```[\s\S]*?```", "", t)
    t = re.sub(r"`[^`]*`", "", t)
    t = re.sub(r"https?://\S+", "", t)
    # Remove markdown symbols
    t = re.sub(r"[\*#_~\[\]\(\)>•]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

async def _synthesize_neural_audio(clean_text: str, voice: str) -> bytes:
    """Generate high-fidelity human audio using Edge-TTS without artificial pitch distortion."""
    # rate=+0%, pitch=+0Hz preserves 100% natural human breathing and intonation
    communicate = edge_tts.Communicate(clean_text, voice, rate="+0%", pitch="+0Hz")
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)

def _speak_worker(clean_text: str, lang: str | None = None):
    """Synthesize and play audio directly to speaker."""
    if not clean_text:
        return

    detected_lang = lang if lang else detect_language(clean_text)
    selected_voice = VOICE_MAP.get(detected_lang, "en-US-JennyNeural")

    try:
        audio_bytes = asyncio.run(_synthesize_neural_audio(clean_text, selected_voice))
        if audio_bytes:
            data, fs = sf.read(io.BytesIO(audio_bytes))
            sd.play(data, fs)
            sd.wait()
            return
    except Exception as e:
        pass

    # Clean fallback without robotic pitch shift
    try:
        import subprocess
        escaped = clean_text.replace("'", "''").replace('"', '`"')
        ps_cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('{escaped}')"
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=10)
    except Exception:
        pass

def speak_text(text: str, lang: str | None = None, non_blocking: bool = False):
    """
    Speak text with natural human voice.
    Supports Hindi, Hinglish, English, and other languages automatically.
    """
    clean = clean_text_for_speech(text)
    if not clean:
        return

    # Cap speech to 2-3 sentences max for natural conversational flow
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    if len(sentences) > 2:
        clean = " ".join(sentences[:2])

    if non_blocking:
        t = threading.Thread(target=_speak_worker, args=(clean, lang), daemon=True)
        t.start()
    else:
        _speak_worker(clean, lang)
