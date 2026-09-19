import os
import sqlite3
from datetime import datetime

import mysql.connector

from config import (
    DB_PROVIDER, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    DB_CONNECT_TIMEOUT, DB_PATH
)


class MemoryStore:
    def __init__(self):
        self.provider = DB_PROVIDER.lower()

    def initialize(self):
        if self.provider == "mysql":
            self._mysql_initialize()
        else:
            self._sqlite_initialize()

    def _mysql_connection(self):
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=DB_CONNECT_TIMEOUT,
            autocommit=True,
            charset="utf8mb4"
        )

    def _mysql_initialize(self):
        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_conversations_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.close()

    def _sqlite_initialize(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH) as con:
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
        if self.provider == "mysql":
            with self._mysql_connection() as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO conversations(role, content) VALUES (%s, %s)",
                    (role, content)
                )
                cur.close()
        else:
            with sqlite3.connect(DB_PATH) as con:
                con.execute(
                    "INSERT INTO messages(role, content, created_at) VALUES (?, ?, ?)",
                    (role, content, datetime.now().isoformat(timespec="seconds"))
                )
                con.commit()

    def recent(self, limit=8):
        if self.provider == "mysql":
            with self._mysql_connection() as con:
                cur = con.cursor()
                cur.execute(
                    "SELECT role, content, created_at FROM conversations "
                    "ORDER BY id DESC LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()
                cur.close()
            rows.reverse()
        else:
            with sqlite3.connect(DB_PATH) as con:
                rows = con.execute(
                    "SELECT role, content, created_at FROM messages "
                    "ORDER BY id DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            rows.reverse()

        return [
            {
                "role": role,
                "content": content,
                "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
            }
            for role, content, created_at in rows
        ]
