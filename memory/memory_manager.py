import re
from memory.short_term import (
    init_short_term_db,
    save_chat_message,
    get_recent_chat_history,
    clear_chat_history
)
from memory.long_term import (
    init_long_term_db,
    save_fact,
    get_all_facts,
    search_facts,
    delete_fact,
    clear_all_facts
)

def init_memory():
    """Initialize all memory tables."""
    init_short_term_db()
    init_long_term_db()

def build_memory_context(user_query: str = "") -> str:
    """
    Build a concise context block of relevant long-term memories
    to inject into the AI system prompt.
    """
    facts = get_all_facts()
    if not facts:
        return ""

    # If query is provided, prioritize matching facts
    relevant_facts = []
    if user_query:
        words = [w.lower() for w in re.findall(r"\w+", user_query) if len(w) > 3]
        for item in facts:
            fact_text = item["fact"].lower()
            if any(w in fact_text for w in words):
                relevant_facts.append(item["fact"])

    # If not enough query matches, take top recent facts
    if len(relevant_facts) < 5:
        for item in facts:
            if item["fact"] not in relevant_facts:
                relevant_facts.append(item["fact"])
            if len(relevant_facts) >= 6:
                break

    if not relevant_facts:
        return ""

    context_lines = ["Important facts about the user and preferences you must remember:"]
    for fact in relevant_facts:
        context_lines.append(f"- {fact}")
    return "\n".join(context_lines)

def detect_and_remember(user_prompt: str) -> str | None:
    """
    Detect if the user is asking the AI to remember a fact, e.g.:
    'remember that my dog's name is Milo'
    'yaad rakhna mera favourite color blue hai'
    'remember I like Python'
    """
    lower = user_prompt.lower().strip()
    match = re.search(r"^(?:please\s+)?(?:remember\s+(?:that\s+)?|yaad\s+rakhna\s+(?:ki\s+)?|note\s+down\s+(?:that\s+)?)(.+)", lower)
    if match:
        fact = match.group(1).strip(" .!?")
        # Normalize 1st person pronouns if straightforward
        if fact.startswith("my "):
            fact = "User's " + fact[3:]
        elif fact.startswith("i am "):
            fact = "User is " + fact[5:]
        elif fact.startswith("i like "):
            fact = "User likes " + fact[7:]
        elif fact.startswith("i love "):
            fact = "User loves " + fact[7:]
        elif fact.startswith("i have "):
            fact = "User has " + fact[7:]

        save_fact(fact, category="user_pref")
        return f"Got it! I have saved this to my memory: \"{fact}\"."
    return None
