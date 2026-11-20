import sqlite3
from datetime import datetime
from config.settings import DB_PATH

def init_short_term_db():
    """Ensure chat_history table exists in SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL DEFAULT 'default',
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_chat_message(role: str, content: str, session_id: str = "default"):
    """Save a chat message to history."""
    init_short_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """, (session_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_recent_chat_history(limit: int = 15, session_id: str = "default") -> list:
    """Retrieve recent chat history for a session formatted for LLM messages list."""
    init_short_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content FROM chat_history
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()

    # Rows were fetched in descending order, reverse so oldest is first
    rows.reverse()
    return [{"role": r[0], "content": r[1]} for r in rows]

def clear_chat_history(session_id: str = None):
    """Clear chat history for a specific session or all sessions."""
    init_short_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if session_id:
        cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    else:
        cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()
