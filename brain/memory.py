import os
import re
import sqlite3
from datetime import datetime
from decimal import Decimal

import mysql.connector

from config import (
    DB_PROVIDER, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
    DB_CONNECT_TIMEOUT, DB_PATH, LONG_TERM_MEMORY_LIMIT,
    MEMORY_SCAN_LIMIT
)


STOPWORDS = {
    "a", "al", "algo", "como", "con", "cuando", "de", "del", "el", "ella",
    "en", "es", "esta", "este", "esto", "la", "las", "lo", "los", "me",
    "mi", "mis", "para", "pero", "por", "que", "se", "si", "sin", "su",
    "sus", "te", "tu", "tus", "un", "una", "y", "ya", "yo"
}


def _float(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, _float(value)))


def _tokens(text):
    words = re.findall(
        r"[a-zA-Z0-9áéíóúñüÁÉÍÓÚÑÜ]+",
        (text or "").lower()
    )
    return {w for w in words if len(w) >= 3 and w not in STOPWORDS}


class MemoryStore:
    def __init__(self):
        self.provider = DB_PROVIDER.lower()

    def initialize(self):
        if self.provider == "mysql":
            self._mysql_initialize()
            self.seed_identity()
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
        statements = [
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_conversations_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS memories (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                memory_type VARCHAR(50) NOT NULL DEFAULT 'episodic',
                content TEXT NOT NULL,
                importance DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                emotional_value DECIMAL(4,3) NOT NULL DEFAULT 0.000,
                source_message_id BIGINT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME NULL,
                access_count INT NOT NULL DEFAULT 0,
                INDEX idx_memories_type (memory_type),
                INDEX idx_memories_importance (importance)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS emotional_state (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                emotion VARCHAR(50) NOT NULL,
                intensity DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                trust DECIMAL(4,3) NOT NULL DEFAULT 0.400,
                energy DECIMAL(4,3) NOT NULL DEFAULT 0.750,
                curiosity DECIMAL(4,3) NOT NULL DEFAULT 0.600,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS identity_profile (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                subject VARCHAR(20) NOT NULL,
                identity_key VARCHAR(80) NOT NULL,
                identity_value TEXT NOT NULL,
                confidence DECIMAL(4,3) NOT NULL DEFAULT 0.800,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL,
                UNIQUE KEY uq_identity_subject_key (subject, identity_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS relationships (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                entity_name VARCHAR(120) NOT NULL,
                relationship_type VARCHAR(50) NOT NULL DEFAULT 'persona',
                affinity DECIMAL(5,3) NOT NULL DEFAULT 0.000,
                trust DECIMAL(5,3) NOT NULL DEFAULT 0.400,
                familiarity DECIMAL(5,3) NOT NULL DEFAULT 0.000,
                notes TEXT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL,
                UNIQUE KEY uq_relationship_entity (entity_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS goals (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(180) NOT NULL,
                description TEXT NULL,
                priority DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                progress DECIMAL(4,3) NOT NULL DEFAULT 0.000,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME NULL,
                INDEX idx_goals_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS internal_events (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                summary TEXT NOT NULL,
                importance DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_internal_events_type (event_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                action VARCHAR(50) NOT NULL,
                reason_summary TEXT NULL,
                confidence DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                status VARCHAR(20) NOT NULL DEFAULT 'completed',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_decisions_action (action)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        ]

        with self._mysql_connection() as con:
            cur = con.cursor()
            for statement in statements:
                cur.execute(statement)
            cur.close()

        self._ensure_mysql_column(
            "memories", "source_message_id", "BIGINT NULL"
        )
        self._ensure_mysql_column(
            "memories", "access_count", "INT NOT NULL DEFAULT 0"
        )
        self._ensure_mysql_column(
            "emotional_state",
            "curiosity",
            "DECIMAL(4,3) NOT NULL DEFAULT 0.600"
        )

    def _ensure_mysql_column(self, table, column, definition):
        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SHOW COLUMNS FROM " + table + " LIKE %s",
                (column,)
            )
            exists = cur.fetchone()

            if not exists:
                cur.execute(
                    "ALTER TABLE " + table +
                    " ADD COLUMN " + column + " " + definition
                )

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
                    "INSERT INTO conversations(role, content) "
                    "VALUES (%s, %s)",
                    (role, content)
                )
                message_id = cur.lastrowid
                cur.close()
                return message_id

        with sqlite3.connect(DB_PATH) as con:
            cur = con.execute(
                "INSERT INTO messages(role, content, created_at) "
                "VALUES (?, ?, ?)",
                (
                    role,
                    content,
                    datetime.now().isoformat(timespec="seconds")
                )
            )
            con.commit()
            return cur.lastrowid

    def recent(self, limit=8):
        if self.provider == "mysql":
            with self._mysql_connection() as con:
                cur = con.cursor()
                cur.execute(
                    "SELECT role, content, created_at "
                    "FROM conversations ORDER BY id DESC LIMIT %s",
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
                "created_at": (
                    created_at.isoformat()
                    if hasattr(created_at, "isoformat")
                    else str(created_at)
                )
            }
            for role, content, created_at in rows
        ]

    def add_memory(
        self,
        memory_type,
        content,
        importance=0.5,
        emotional_value=0.0,
        source_message_id=None
    ):
        if self.provider != "mysql" or not content:
            return None

        memory_type = (memory_type or "episodic")[:50]
        content = content.strip()
        importance = _clamp(importance)
        emotional_value = max(-1.0, min(1.0, _float(emotional_value)))

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id FROM memories "
                "WHERE memory_type=%s AND content=%s LIMIT 1",
                (memory_type, content)
            )
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    "UPDATE memories "
                    "SET importance=GREATEST(importance,%s), "
                    "last_accessed=NOW(), access_count=access_count+1 "
                    "WHERE id=%s",
                    (importance, existing[0])
                )
                memory_id = existing[0]
            else:
                cur.execute(
                    "INSERT INTO memories("
                    "memory_type, content, importance, emotional_value, "
                    "source_message_id"
                    ") VALUES (%s,%s,%s,%s,%s)",
                    (
                        memory_type,
                        content,
                        importance,
                        emotional_value,
                        source_message_id
                    )
                )
                memory_id = cur.lastrowid

            cur.close()
            return memory_id

    def search_memories(self, query, limit=LONG_TERM_MEMORY_LIMIT):
        if self.provider != "mysql":
            return []

        query_tokens = _tokens(query)

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, memory_type, content, importance, "
                "emotional_value, created_at, access_count "
                "FROM memories "
                "ORDER BY importance DESC, id DESC LIMIT %s",
                (MEMORY_SCAN_LIMIT,)
            )
            rows = cur.fetchall()
            cur.close()

        scored = []

        for row in rows:
            memory_tokens = _tokens(row[2])
            overlap = len(query_tokens & memory_tokens)
            importance = _float(row[3], 0.5)
            access_count = int(row[6] or 0)

            lexical = (
                overlap / max(1, len(query_tokens))
                if query_tokens else 0.0
            )

            score = (
                lexical * 2.4 +
                importance +
                min(access_count, 10) * 0.02
            )

            if overlap > 0 or importance >= 0.82:
                scored.append((score, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = scored[:limit]

        results = []
        ids = []

        for score, row in selected:
            ids.append(row[0])
            results.append({
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "importance": _float(row[3]),
                "emotional_value": _float(row[4]),
                "created_at": (
                    row[5].isoformat()
                    if hasattr(row[5], "isoformat")
                    else str(row[5])
                ),
                "relevance": round(score, 3)
            })

        if ids:
            placeholders = ",".join(["%s"] * len(ids))

            with self._mysql_connection() as con:
                cur = con.cursor()
                cur.execute(
                    "UPDATE memories SET last_accessed=NOW(), "
                    "access_count=access_count+1 "
                    "WHERE id IN (" + placeholders + ")",
                    tuple(ids)
                )
                cur.close()

        return results

    def seed_identity(self):
        self.upsert_identity("eva", "name", "EVA", 1.0)
        self.upsert_identity(
            "eva",
            "nature",
            "Agente artificial experimental local con memoria persistente.",
            1.0
        )
        self.upsert_identity(
            "eva",
            "purpose",
            "Conversar, aprender de las interacciones y conservar recuerdos seleccionados.",
            0.95
        )

        if self.provider == "mysql":
            with self._mysql_connection() as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT IGNORE INTO relationships("
                    "entity_name, relationship_type, affinity, trust, "
                    "familiarity, notes"
                    ") VALUES ("
                    "'usuario_principal','persona',0.100,0.400,0.050,"
                    "'Relacion principal de EVA con su usuario.'"
                    ")"
                )
                cur.close()

    def upsert_identity(
        self,
        subject,
        key,
        value,
        confidence=0.8
    ):
        if self.provider != "mysql" or not value:
            return

        subject = "user" if subject == "user" else "eva"
        key = re.sub(
            r"[^a-z0-9_]+",
            "_",
            (key or "fact").lower()
        ).strip("_")[:80]
        value = str(value).strip()
        confidence = _clamp(confidence)

        if not key or not value:
            return

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO identity_profile("
                "subject, identity_key, identity_value, confidence, updated_at"
                ") VALUES (%s,%s,%s,%s,NOW()) "
                "ON DUPLICATE KEY UPDATE "
                "identity_value=VALUES(identity_value), "
                "confidence=GREATEST(confidence,VALUES(confidence)), "
                "updated_at=NOW()",
                (subject, key, value, confidence)
            )
            cur.close()

    def get_identity(self, subject=None):
        if self.provider != "mysql":
            return []

        sql = (
            "SELECT subject, identity_key, identity_value, confidence "
            "FROM identity_profile"
        )
        params = ()

        if subject in {"eva", "user"}:
            sql += " WHERE subject=%s"
            params = (subject,)

        sql += " ORDER BY subject, id"

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()

        return [
            {
                "subject": row[0],
                "key": row[1],
                "value": row[2],
                "confidence": _float(row[3])
            }
            for row in rows
        ]

    def get_relationship(self, entity_name="usuario_principal"):
        if self.provider != "mysql":
            return {
                "entity_name": entity_name,
                "affinity": 0.0,
                "trust": 0.4,
                "familiarity": 0.0,
                "notes": ""
            }

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT entity_name, relationship_type, affinity, trust, "
                "familiarity, notes "
                "FROM relationships WHERE entity_name=%s LIMIT 1",
                (entity_name,)
            )
            row = cur.fetchone()
            cur.close()

        if not row:
            return {
                "entity_name": entity_name,
                "relationship_type": "persona",
                "affinity": 0.0,
                "trust": 0.4,
                "familiarity": 0.0,
                "notes": ""
            }

        return {
            "entity_name": row[0],
            "relationship_type": row[1],
            "affinity": _float(row[2]),
            "trust": _float(row[3]),
            "familiarity": _float(row[4]),
            "notes": row[5] or ""
        }

    def update_relationship(
        self,
        entity_name="usuario_principal",
        affinity_delta=0.0,
        trust_delta=0.0,
        familiarity_delta=0.0,
        note=""
    ):
        if self.provider != "mysql":
            return

        current = self.get_relationship(entity_name)

        affinity = max(
            -1.0,
            min(
                1.0,
                current["affinity"] + _float(affinity_delta)
            )
        )
        trust = _clamp(
            current["trust"] + _float(trust_delta)
        )
        familiarity = _clamp(
            current["familiarity"] + _float(familiarity_delta)
        )

        notes = current.get("notes", "")
        clean_note = (note or "").strip()

        if clean_note and clean_note not in notes:
            notes = (notes + " " + clean_note).strip()
            notes = notes[-1200:]

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO relationships("
                "entity_name, relationship_type, affinity, trust, "
                "familiarity, notes, updated_at"
                ") VALUES (%s,'persona',%s,%s,%s,%s,NOW()) "
                "ON DUPLICATE KEY UPDATE "
                "affinity=VALUES(affinity), "
                "trust=VALUES(trust), "
                "familiarity=VALUES(familiarity), "
                "notes=VALUES(notes), "
                "updated_at=NOW()",
                (
                    entity_name,
                    affinity,
                    trust,
                    familiarity,
                    notes
                )
            )
            cur.close()

    def latest_emotional_state(self):
        if self.provider != "mysql":
            return None

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT emotion, intensity, trust, energy, curiosity "
                "FROM emotional_state ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            cur.close()

        if not row:
            return None

        return {
            "emotion": row[0],
            "intensity": _float(row[1], 0.5),
            "trust": _float(row[2], 0.4),
            "energy": _float(row[3], 0.75),
            "curiosity": _float(row[4], 0.6)
        }

    def save_emotional_state(self, state):
        if self.provider != "mysql":
            return

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO emotional_state("
                "emotion, intensity, trust, energy, curiosity"
                ") VALUES (%s,%s,%s,%s,%s)",
                (
                    state.get("emotion", "neutral"),
                    _clamp(state.get("intensity", 0.5)),
                    _clamp(state.get("trust", 0.4)),
                    _clamp(state.get("energy", 0.75)),
                    _clamp(state.get("curiosity", 0.6))
                )
            )
            cur.close()

    def add_goal(self, title, description="", priority=0.5):
        if self.provider != "mysql" or not title:
            return None

        title = title.strip()[:180]
        description = (description or "").strip()
        priority = _clamp(priority)

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id FROM goals "
                "WHERE title=%s AND status='active' LIMIT 1",
                (title,)
            )
            existing = cur.fetchone()

            if existing:
                cur.close()
                return existing[0]

            cur.execute(
                "INSERT INTO goals(title, description, priority) "
                "VALUES (%s,%s,%s)",
                (title, description, priority)
            )
            goal_id = cur.lastrowid
            cur.close()
            return goal_id

    def get_active_goals(self, limit=5):
        if self.provider != "mysql":
            return []

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, title, description, priority, progress "
                "FROM goals WHERE status='active' "
                "ORDER BY priority DESC, id DESC LIMIT %s",
                (limit,)
            )
            rows = cur.fetchall()
            cur.close()

        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2] or "",
                "priority": _float(row[3]),
                "progress": _float(row[4])
            }
            for row in rows
        ]

    def log_internal_event(
        self,
        event_type,
        summary,
        importance=0.5
    ):
        if self.provider != "mysql" or not summary:
            return

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO internal_events("
                "event_type, summary, importance"
                ") VALUES (%s,%s,%s)",
                (
                    (event_type or "reflection")[:50],
                    summary.strip(),
                    _clamp(importance)
                )
            )
            cur.close()

    def save_decision(
        self,
        action,
        reason_summary="",
        confidence=0.5,
        status="completed"
    ):
        if (
            self.provider != "mysql"
            or not action
            or action == "none"
        ):
            return

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO decisions("
                "action, reason_summary, confidence, status"
                ") VALUES (%s,%s,%s,%s)",
                (
                    action[:50],
                    (reason_summary or "").strip(),
                    _clamp(confidence),
                    (status or "completed")[:20]
                )
            )
            cur.close()


    def list_recent_memories(self, limit=10):
        if self.provider != "mysql":
            return []

        with self._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, memory_type, content, importance, "
                "emotional_value, created_at, access_count "
                "FROM memories ORDER BY id DESC LIMIT %s",
                (limit,)
            )
            rows = cur.fetchall()
            cur.close()

        return [
            {
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "importance": _float(row[3]),
                "emotional_value": _float(row[4]),
                "created_at": (
                    row[5].isoformat()
                    if hasattr(row[5], "isoformat")
                    else str(row[5])
                ),
                "access_count": int(row[6] or 0)
            }
            for row in rows
        ]

    def cognitive_context(self, user_message):
        return {
            "identity": self.get_identity(),
            "relationship": self.get_relationship(),
            "memories": self.search_memories(user_message),
            "goals": self.get_active_goals(),
            "emotion": self.latest_emotional_state()
        }

    def stats(self):
        if self.provider != "mysql":
            return {}

        tables = [
            "conversations",
            "memories",
            "identity_profile",
            "relationships",
            "emotional_state",
            "goals",
            "internal_events",
            "decisions"
        ]

        result = {}

        with self._mysql_connection() as con:
            cur = con.cursor()

            for table in tables:
                cur.execute("SELECT COUNT(*) FROM " + table)
                result[table] = int(cur.fetchone()[0])

            cur.close()

        return result
