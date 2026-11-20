import sounddevice as sd
import numpy as np
import speech_recognition as sr
import time

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"

def record_audio(duration: float = 6.0, silence_timeout: float = 1.2, energy_threshold: float = 280.0) -> np.ndarray | None:
    """
    Record mono audio from default microphone with dynamic silence detection.
    Stops as soon as user finishes speaking (1.2s silence).
    """
    chunk_duration = 0.1
    chunk_samples = int(SAMPLE_RATE * chunk_duration)
    max_chunks = int(duration / chunk_duration)
    silence_chunks_limit = int(silence_timeout / chunk_duration)

    recorded_chunks = []
    has_spoken = False
    silence_count = 0

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE) as stream:
            for _ in range(max_chunks):
                chunk, overflowed = stream.read(chunk_samples)
                energy = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if energy > energy_threshold:
                    has_spoken = True
                    silence_count = 0
                    recorded_chunks.append(chunk)
                else:
                    if has_spoken:
                        recorded_chunks.append(chunk)
                        silence_count += 1
                        if silence_count >= silence_chunks_limit:
                            break
                    else:
                        if len(recorded_chunks) >= 2:
                            recorded_chunks.pop(0)
                        recorded_chunks.append(chunk)

        if not has_spoken or not recorded_chunks:
            return None

        audio_data = np.concatenate(recorded_chunks, axis=0)

        # Dynamic gain normalization
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            scale = min(32000.0 / max_val, 3.5)
            audio_data = (audio_data.astype(np.float32) * scale).clip(-32768, 32767).astype(np.int16)

        return audio_data

    except Exception as e:
        return None

def listen_and_transcribe(duration: float = 6.5, preferred_lang: str = "en-IN") -> str | None:
    """
    Transcribe speech in any language using SpeechRecognition.
    Supports English, Hindi, Hinglish, and multilingual speech.
    """
    audio_np = record_audio(duration=duration)
    if audio_np is None or len(audio_np) == 0:
        return None

    raw_bytes = audio_np.tobytes()
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(raw_bytes, SAMPLE_RATE, 2)

    # Multi-language recognition pipeline
    languages_to_try = [preferred_lang, "hi-IN", "en-US"]
    if preferred_lang not in languages_to_try:
        languages_to_try.insert(0, preferred_lang)

    for lang in languages_to_try:
        try:
            text = recognizer.recognize_google(audio_data, language=lang)
            if text and text.strip():
                return text.strip()
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            break
        except Exception:
            continue

    return None

def get_speech_recognition_html() -> str:
    """Web fallback component."""
    return "<p>Voice recognition widget</p>"
