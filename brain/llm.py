import ollama
import sys
import re
from datetime import datetime
from personality.identity import get_identity
from memory.memory_manager import build_memory_context, detect_and_remember
from memory.short_term import save_chat_message
from tools.system_tools import execute_tool_intent, get_current_time_info
from voice.text_to_speech import detect_language
from config.settings import DEFAULT_MODEL

# High-speed conversational inference options
FAST_OPTIONS = {
    "num_thread": 4,
    "num_ctx": 512,
    "num_predict": 65,       # Keeps answers crisp and fast (1-2 sentences)
    "temperature": 0.4,      # Focused, direct responses
    "top_k": 30,
    "top_p": 0.85
}

def get_available_models() -> list[str]:
    """Retrieve list of locally installed Ollama models."""
    try:
        res = ollama.list()
        models = []
        model_list = getattr(res, "models", res)
        for item in model_list:
            if hasattr(item, "model"):
                models.append(item.model)
            elif isinstance(item, dict):
                models.append(item.get("name") or item.get("model", "unknown"))
        return models if models else [DEFAULT_MODEL]
    except Exception:
        return [DEFAULT_MODEL]

def build_language_system_prompt(identity: dict, user_query: str = "") -> tuple[str, str]:
    """
    Build conversational system prompt enforcing automatic language mirroring.
    Returns (system_prompt, detected_language).
    """
    name = identity.get("name", "Assistant")
    user_name = identity.get("user_name", "Friend")
    memory_context = build_memory_context(user_query)
    lang = detect_language(user_query)

    if lang in ["hi", "hinglish"]:
        instruction = (
            f"You are {name}, a sweet, friendly AI companion for {user_name}. "
            "The user asked in Hindi/Hinglish. "
            "Reply directly in sweet Hindi or conversational Hinglish in 1 short line. "
            "Do not write English lectures or repeat instructions."
        )
    elif lang == "es":
        instruction = f"You are {name}, a friendly AI companion for {user_name}. Reply in Spanish in 1 short sentence."
    elif lang == "fr":
        instruction = f"You are {name}, a friendly AI companion for {user_name}. Reply in French in 1 short sentence."
    else:
        instruction = (
            f"You are {name}, a sweet, friendly AI companion for {user_name} (like Siri). "
            "Reply in sweet, natural conversational English. "
            "Give direct, helpful answers in 1 or 2 short sentences. Never write essays or bullet lists."
        )

    parts = [instruction]
    if memory_context:
        parts.append(memory_context)

    return "\n".join(parts), lang

def clean_response(text: str) -> str:
    """Trim conversational artifacts and constrain to 2 sentences."""
    t = text.strip()
    t = re.sub(r"^(?:Assistant|AI|User|System):\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(?:Sure,?\s*(?:here'?s|here is|here's a translation|let me explain).*?:?\s*)", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\n+(?:Assistant|AI|User):\s*.*$", "", t, flags=re.IGNORECASE)

    # Stop at max 2 sentences
    sentences = re.split(r"(?<=[.!?])\s+", t)
    if len(sentences) > 2:
        t = " ".join(sentences[:2])
    return t.strip()

def ask_ai(user_message: str, chat_history: list = None, model: str = DEFAULT_MODEL, stream: bool = False, session_id: str = "default"):
    """
    Process query with tool matching, memory storage, and language-aware fast LLM reasoning.
    """
    if chat_history is None:
        chat_history = []

    # 1. Instant check for memory commands
    memory_ack = detect_and_remember(user_message)
    if memory_ack:
        save_chat_message("user", user_message, session_id=session_id)
        save_chat_message("assistant", memory_ack, session_id=session_id)
        if stream:
            def simple_gen():
                yield memory_ack
            return simple_gen()
        return memory_ack

    # 2. Instant check for system tool commands
    tool_output = execute_tool_intent(user_message)
    if tool_output:
        save_chat_message("user", user_message, session_id=session_id)
        save_chat_message("assistant", tool_output, session_id=session_id)
        if stream:
            def tool_gen():
                yield tool_output
            return tool_gen()
        return tool_output

    # 3. Dynamic multilingual system prompt
    identity = get_identity()
    system_prompt, detected_lang = build_language_system_prompt(identity, user_query=user_message)

    messages = [{"role": "system", "content": system_prompt}]

    for msg in chat_history[-2:]:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})
    clean_model = model if model else DEFAULT_MODEL

    try:
        response = ollama.chat(
            model=clean_model,
            messages=messages,
            stream=False,
            options=FAST_OPTIONS,
            keep_alive="60m"
        )
        raw_reply = response.get("message", {}).get("content", "")
        reply = clean_response(raw_reply)
        if not reply:
            reply = "Haan ji, main sun rahi hoon! Aur bataiye?" if detected_lang in ["hi", "hinglish"] else "I'm right here! How can I help?"

        save_chat_message("user", user_message, session_id=session_id)
        save_chat_message("assistant", reply, session_id=session_id)

        if stream:
            def gen():
                yield reply
            return gen()
        return reply

    except Exception as e:
        err = str(e)
        if "connection refused" in err.lower() or "11434" in err:
            return "Ollama is not running. Please start it with 'ollama serve'."
        return f"Error: {err}"