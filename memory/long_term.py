import sqlite3
from datetime import datetime
from config.settings import DB_PATH

def init_long_term_db():
    """Ensure user_facts table exists in SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL DEFAULT 'general',
            fact TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_fact(fact: str, category: str = "general") -> bool:
    """Store a persistent fact about the user or preferences."""
    init_long_term_db()
    fact_clean = fact.strip()
    if not fact_clean:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO user_facts (category, fact, created_at)
            VALUES (?, ?, ?)
        """, (category, fact_clean, datetime.now().isoformat()))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_all_facts() -> list:
    """Retrieve all stored user facts."""
    init_long_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, category, fact, created_at FROM user_facts
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": r[0], "category": r[1], "fact": r[2], "created_at": r[3]}
        for r in rows
    ]

def search_facts(query: str) -> list:
    """Search user facts by keyword."""
    init_long_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    pattern = f"%{query}%"
    cursor.execute("""
        SELECT id, category, fact, created_at FROM user_facts
        WHERE fact LIKE ? OR category LIKE ?
        ORDER BY id DESC
    """, (pattern, pattern))
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": r[0], "category": r[1], "fact": r[2], "created_at": r[3]}
        for r in rows
    ]

def delete_fact(fact_id: int) -> bool:
    """Delete a fact by its ID."""
    init_long_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_facts WHERE id = ?", (fact_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def clear_all_facts():
    """Delete all persistent facts."""
    init_long_term_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_facts")
    conn.commit()
    conn.close()
