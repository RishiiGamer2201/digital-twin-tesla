"""
SQLite-backed long-term memory. Stores conversation summaries and key facts
extracted from past sessions. Supports keyword-based retrieval.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = "memory.db"


class LongTermMemory:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    summary TEXT,
                    topics TEXT,        -- JSON array of topic strings
                    entities TEXT,      -- JSON array of named entities
                    message_count INTEGER,
                    user_name TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    content TEXT NOT NULL,
                    category TEXT,      -- e.g. "preference", "question", "concept_discussed"
                    importance REAL DEFAULT 0.5,
                    created_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            conn.commit()

    def save_session(
        self, session_id: str, summary: str, topics: List[str],
        entities: List[str], message_count: int, user_name: str = ""
    ):
        """Save a session summary to long-term memory."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO sessions
                   (id, timestamp, summary, topics, entities, message_count, user_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, datetime.now().isoformat(), summary,
                 json.dumps(topics), json.dumps(entities), message_count, user_name)
            )
            conn.commit()

    def save_fact(
        self, session_id: str, content: str, category: str,
        importance: float = 0.5
    ):
        """Save an individual fact extracted from a conversation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO facts (session_id, content, category, importance, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, content, category, importance,
                 datetime.now().isoformat())
            )
            conn.commit()

    def get_relevant_memories(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Simple keyword-based retrieval from long-term memory.
        Returns the most relevant past session summaries.
        """
        keywords = [w.lower() for w in query.split() if len(w) > 3]
        if not keywords:
            return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Search summaries and topics for keyword matches
            placeholders = " OR ".join(
                ["LOWER(summary) LIKE ?" for _ in keywords] +
                ["LOWER(topics) LIKE ?" for _ in keywords]
            )
            params = [f"%{kw}%" for kw in keywords] * 2
            rows = conn.execute(
                f"SELECT * FROM sessions WHERE {placeholders} "
                f"ORDER BY timestamp DESC LIMIT ?",
                params + [limit]
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_sessions(self) -> List[Dict]:
        """Return all stored sessions, newest first."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY timestamp DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_facts(self, limit: int = 10) -> List[Dict]:
        """Return most recent facts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM facts ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated facts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM facts WHERE session_id = ?", (session_id,))
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
