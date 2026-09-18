import os
import sqlite3
from datetime import datetime
from config import DB_PATH

class MemoryStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def initialize(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            con.commit()

    def add(self, role, content):
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT INTO messages(role, content, created_at) VALUES (?, ?, ?)",
                (role, content, datetime.now().isoformat(timespec="seconds"))
            )
            con.commit()

    def recent(self, limit=8):
        with sqlite3.connect(self.db_path) as con:
            rows = con.execute(
                "SELECT role, content, created_at FROM messages ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [
            {"role": role, "content": content, "created_at": created_at}
            for role, content, created_at in reversed(rows)
        ]
