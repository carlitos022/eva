import hashlib
import json
from datetime import datetime, timezone

from brain.embeddings import OllamaEmbeddingClient
from brain.memory import _clamp, _float, _tokens
from config import (
    LONG_TERM_MEMORY_LIMIT,
    MEMORY_SCAN_LIMIT,
    MEMORY_TREE_REBUILD_EVERY,
)


def _sha256(value):
    return hashlib.sha256(
        (value or "").strip().lower().encode("utf-8")
    ).hexdigest()


class MemoryCortex:
    """
    Capa cognitiva sobre MemoryStore.

    Mantiene compatibilidad con la memoria v0.3 y agrega:
    - embeddings opcionales
    - recuperacion hibrida
    - entidades y relaciones
    - arbol compacto de memoria
    - tareas vinculables a objetivos
    """

    def __init__(self, store):
        self.store = store
        self.embedder = OllamaEmbeddingClient()
        self._memories_since_tree = 0

    def initialize(self):
        if self.store.provider != "mysql":
            return

        self.store._ensure_mysql_column(
            "memories", "embedding", "LONGTEXT NULL"
        )
        self.store._ensure_mysql_column(
            "memories",
            "strength",
            "DECIMAL(4,3) NOT NULL DEFAULT 0.500",
        )
        self.store._ensure_mysql_column(
            "memories", "content_hash", "CHAR(64) NULL"
        )
        self.store._ensure_mysql_column(
            "memories", "updated_at", "DATETIME NULL"
        )

        statements = [
            """
            CREATE TABLE IF NOT EXISTS entities (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                canonical_key CHAR(64) NOT NULL,
                canonical_name VARCHAR(180) NOT NULL,
                entity_type VARCHAR(50) NOT NULL DEFAULT 'other',
                summary TEXT NULL,
                importance DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL,
                UNIQUE KEY uq_entities_key (canonical_key),
                INDEX idx_entities_name (canonical_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS entity_relations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                relation_key CHAR(64) NOT NULL,
                source_entity_id BIGINT NOT NULL,
                relation_type VARCHAR(80) NOT NULL,
                target_entity_id BIGINT NOT NULL,
                confidence DECIMAL(4,3) NOT NULL DEFAULT 0.700,
                evidence_memory_id BIGINT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL,
                UNIQUE KEY uq_entity_relation_key (relation_key),
                INDEX idx_relation_source (source_entity_id),
                INDEX idx_relation_target (target_entity_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS memory_tree (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                path_key CHAR(64) NOT NULL,
                path VARCHAR(180) NOT NULL,
                branch_type VARCHAR(50) NOT NULL DEFAULT 'memory',
                summary TEXT NOT NULL,
                item_count INT NOT NULL DEFAULT 0,
                importance DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                updated_at DATETIME NULL,
                UNIQUE KEY uq_memory_tree_key (path_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                goal_id BIGINT NULL,
                title VARCHAR(180) NOT NULL,
                description TEXT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'pending',
                priority DECIMAL(4,3) NOT NULL DEFAULT 0.500,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL,
                INDEX idx_tasks_status (status),
                INDEX idx_tasks_goal (goal_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ]

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            for statement in statements:
                cur.execute(statement)
            cur.close()

        self._backfill_hashes()
        self.rebuild_memory_tree()

    def _backfill_hashes(self, limit=1000):
        if self.store.provider != "mysql":
            return

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, content FROM memories "
                "WHERE content_hash IS NULL OR content_hash='' "
                "ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()

            for memory_id, content in rows:
                cur.execute(
                    "UPDATE memories SET content_hash=%s "
                    "WHERE id=%s",
                    (_sha256(content), memory_id),
                )
            cur.close()

    def _encode_embedding(self, vector):
        if not vector:
            return None
        return json.dumps(vector, separators=(",", ":"))

    def _decode_embedding(self, raw):
        if not raw:
            return None
        try:
            vector = json.loads(raw)
            if isinstance(vector, list):
                return [float(value) for value in vector]
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        return None

    def remember(
        self,
        memory_type,
        content,
        importance=0.5,
        emotional_value=0.0,
        source_message_id=None,
    ):
        memory_id = self.store.add_memory(
            memory_type,
            content,
            importance,
            emotional_value,
            source_message_id,
        )

        if not memory_id or self.store.provider != "mysql":
            return memory_id

        vector = self.embedder.embed(content)
        encoded = self._encode_embedding(vector)

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "UPDATE memories SET content_hash=%s, "
                "strength=GREATEST(strength,%s), "
                "embedding=COALESCE(%s, embedding), "
                "updated_at=NOW() WHERE id=%s",
                (
                    _sha256(content),
                    _clamp(importance),
                    encoded,
                    memory_id,
                ),
            )
            cur.close()

        self._memories_since_tree += 1
        if (
            MEMORY_TREE_REBUILD_EVERY > 0
            and self._memories_since_tree >= MEMORY_TREE_REBUILD_EVERY
        ):
            self.rebuild_memory_tree()
            self._memories_since_tree = 0

        return memory_id

    def _candidate_rows(self):
        if self.store.provider != "mysql":
            return []

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, memory_type, content, importance, "
                "emotional_value, created_at, access_count, "
                "embedding, strength "
                "FROM memories "
                "ORDER BY importance DESC, id DESC LIMIT %s",
                (MEMORY_SCAN_LIMIT,),
            )
            rows = cur.fetchall()
            cur.close()
        return rows

    def recall(self, query, limit=LONG_TERM_MEMORY_LIMIT):
        if self.store.provider != "mysql":
            return self.store.search_memories(query, limit)

        query_tokens = _tokens(query)
        query_vector = self.embedder.embed(query)
        now = datetime.now(timezone.utc)
        scored = []

        for row in self._candidate_rows():
            (
                memory_id,
                memory_type,
                content,
                importance_raw,
                emotional_raw,
                created_at,
                access_count_raw,
                embedding_raw,
                strength_raw,
            ) = row

            importance = _clamp(importance_raw)
            emotional = min(1.0, abs(_float(emotional_raw)))
            strength = _clamp(strength_raw, 0.0, 1.0)
            access_count = int(access_count_raw or 0)

            memory_tokens = _tokens(content)
            overlap = len(query_tokens & memory_tokens)
            lexical = (
                overlap / max(1, len(query_tokens))
                if query_tokens else 0.0
            )

            semantic = 0.0
            memory_vector = self._decode_embedding(embedding_raw)
            if query_vector and memory_vector:
                semantic = max(
                    0.0,
                    self.embedder.cosine(query_vector, memory_vector),
                )

            recency = 0.0
            if created_at:
                if getattr(created_at, "tzinfo", None) is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                days = max(0.0, (now - created_at).total_seconds() / 86400)
                recency = 1.0 / (1.0 + days / 45.0)

            reinforcement = min(1.0, access_count / 10.0)

            if query_vector and memory_vector:
                score = (
                    semantic * 0.42
                    + lexical * 0.20
                    + importance * 0.16
                    + strength * 0.07
                    + recency * 0.06
                    + reinforcement * 0.05
                    + emotional * 0.04
                )
                relevant = (
                    semantic >= 0.48
                    or lexical > 0.0
                    or importance >= 0.82
                )
            else:
                score = (
                    lexical * 0.45
                    + importance * 0.27
                    + strength * 0.10
                    + recency * 0.08
                    + reinforcement * 0.06
                    + emotional * 0.04
                )
                relevant = lexical > 0.0 or importance >= 0.82

            if relevant:
                scored.append((score, row, semantic, lexical))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = scored[:limit]
        ids = []
        results = []

        for score, row, semantic, lexical in selected:
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
                "relevance": round(float(score), 4),
                "semantic": round(float(semantic), 4),
                "lexical": round(float(lexical), 4),
            })

        if ids:
            placeholders = ",".join(["%s"] * len(ids))
            with self.store._mysql_connection() as con:
                cur = con.cursor()
                cur.execute(
                    "UPDATE memories SET last_accessed=NOW(), "
                    "access_count=access_count+1, "
                    "strength=LEAST(1.000,strength+0.010) "
                    "WHERE id IN (" + placeholders + ")",
                    tuple(ids),
                )
                cur.close()

        return results

    def upsert_entity(
        self,
        name,
        entity_type="other",
        summary="",
        importance=0.5,
    ):
        if self.store.provider != "mysql":
            return None

        name = (name or "").strip()[:180]
        entity_type = (entity_type or "other").strip().lower()[:50]
        if not name:
            return None

        key = _sha256(f"{entity_type}:{name}")

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO entities("
                "canonical_key, canonical_name, entity_type, summary, "
                "importance, updated_at"
                ") VALUES (%s,%s,%s,%s,%s,NOW()) "
                "ON DUPLICATE KEY UPDATE "
                "summary=CASE WHEN VALUES(summary)<>'' "
                "THEN VALUES(summary) ELSE summary END, "
                "importance=GREATEST(importance,VALUES(importance)), "
                "updated_at=NOW()",
                (
                    key,
                    name,
                    entity_type,
                    (summary or "").strip()[:2000],
                    _clamp(importance),
                ),
            )
            cur.execute(
                "SELECT id FROM entities WHERE canonical_key=%s LIMIT 1",
                (key,),
            )
            row = cur.fetchone()
            cur.close()

        return row[0] if row else None

    def _entity_id_by_name(self, name):
        if self.store.provider != "mysql" or not name:
            return None

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id FROM entities "
                "WHERE LOWER(canonical_name)=LOWER(%s) "
                "ORDER BY importance DESC LIMIT 1",
                ((name or "").strip(),),
            )
            row = cur.fetchone()
            cur.close()
        return row[0] if row else None

    def link_entities(
        self,
        source,
        relation,
        target,
        confidence=0.7,
        evidence_memory_id=None,
    ):
        if self.store.provider != "mysql":
            return None

        relation = (relation or "").strip().lower()[:80]
        if not source or not target or not relation:
            return None

        source_id = (
            self._entity_id_by_name(source)
            or self.upsert_entity(source)
        )
        target_id = (
            self._entity_id_by_name(target)
            or self.upsert_entity(target)
        )

        if not source_id or not target_id:
            return None

        relation_key = _sha256(
            f"{source_id}:{relation}:{target_id}"
        )

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO entity_relations("
                "relation_key, source_entity_id, relation_type, "
                "target_entity_id, confidence, evidence_memory_id, updated_at"
                ") VALUES (%s,%s,%s,%s,%s,%s,NOW()) "
                "ON DUPLICATE KEY UPDATE "
                "confidence=GREATEST(confidence,VALUES(confidence)), "
                "evidence_memory_id=COALESCE("
                "VALUES(evidence_memory_id),evidence_memory_id"
                "), updated_at=NOW()",
                (
                    relation_key,
                    source_id,
                    relation,
                    target_id,
                    _clamp(confidence),
                    evidence_memory_id,
                ),
            )
            relation_id = cur.lastrowid
            cur.close()
        return relation_id

    def list_entities(self, limit=20):
        if self.store.provider != "mysql":
            return []

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, canonical_name, entity_type, summary, importance "
                "FROM entities ORDER BY importance DESC, id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
            cur.close()

        return [
            {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "summary": row[3] or "",
                "importance": _float(row[4]),
            }
            for row in rows
        ]

    def find_entities(self, query, limit=6):
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        scored = []
        for entity in self.list_entities(60):
            text_tokens = _tokens(
                entity["name"] + " " + entity["summary"]
            )
            overlap = len(query_tokens & text_tokens)
            if overlap:
                score = (
                    overlap / max(1, len(query_tokens))
                    + entity["importance"] * 0.25
                )
                scored.append((score, entity))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [entity for _, entity in scored[:limit]]

    def rebuild_memory_tree(self):
        if self.store.provider != "mysql":
            return []

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT memory_type, COUNT(*), MAX(importance) "
                "FROM memories GROUP BY memory_type "
                "ORDER BY MAX(importance) DESC, COUNT(*) DESC"
            )
            groups = cur.fetchall()

            total = 0
            branches = []

            for memory_type, count, max_importance in groups:
                total += int(count or 0)
                cur.execute(
                    "SELECT content FROM memories "
                    "WHERE memory_type=%s "
                    "ORDER BY importance DESC, id DESC LIMIT 3",
                    (memory_type,),
                )
                highlights = [
                    (row[0] or "").strip()
                    for row in cur.fetchall()
                    if row and row[0]
                ]

                summary = " | ".join(highlights)[:2400]
                path = f"memories/{memory_type}"[:180]
                path_key = _sha256(path)

                cur.execute(
                    "INSERT INTO memory_tree("
                    "path_key,path,branch_type,summary,item_count,"
                    "importance,updated_at"
                    ") VALUES (%s,%s,'memory',%s,%s,%s,NOW()) "
                    "ON DUPLICATE KEY UPDATE "
                    "summary=VALUES(summary), "
                    "item_count=VALUES(item_count), "
                    "importance=VALUES(importance), "
                    "updated_at=NOW()",
                    (
                        path_key,
                        path,
                        summary or "Sin resumen.",
                        int(count or 0),
                        _clamp(max_importance),
                    ),
                )
                branches.append(path)

            root_summary = (
                f"EVA conserva {total} recuerdos distribuidos "
                f"en {len(groups)} ramas."
            )
            cur.execute(
                "INSERT INTO memory_tree("
                "path_key,path,branch_type,summary,item_count,"
                "importance,updated_at"
                ") VALUES (%s,'memories','root',%s,%s,1.000,NOW()) "
                "ON DUPLICATE KEY UPDATE "
                "summary=VALUES(summary),item_count=VALUES(item_count),"
                "importance=VALUES(importance),updated_at=NOW()",
                (_sha256("memories"), root_summary, total),
            )
            cur.close()

        return branches

    def get_memory_tree(self, limit=12):
        if self.store.provider != "mysql":
            return []

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT path, branch_type, summary, item_count, importance "
                "FROM memory_tree "
                "ORDER BY CASE WHEN branch_type='root' THEN 0 ELSE 1 END, "
                "importance DESC, item_count DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
            cur.close()

        return [
            {
                "path": row[0],
                "type": row[1],
                "summary": row[2],
                "items": int(row[3] or 0),
                "importance": _float(row[4]),
            }
            for row in rows
        ]

    def get_tasks(self, limit=20):
        if self.store.provider != "mysql":
            return []

        with self.store._mysql_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, goal_id, title, description, status, priority "
                "FROM tasks WHERE status<>'completed' "
                "ORDER BY priority DESC, id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
            cur.close()

        return [
            {
                "id": row[0],
                "goal_id": row[1],
                "title": row[2],
                "description": row[3] or "",
                "status": row[4],
                "priority": _float(row[5]),
            }
            for row in rows
        ]

    def apply_archive(self, archive, source_message_id=None):
        if not isinstance(archive, dict):
            return {"memories": 0, "entities": 0, "goals": 0}

        counters = {"memories": 0, "entities": 0, "goals": 0}

        for item in (archive.get("memories") or [])[:8]:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            importance = _clamp(item.get("importance", 0.5))
            if not content or importance < 0.45:
                continue

            self.remember(
                str(item.get("type", "episodic"))[:50],
                content[:2000],
                importance,
                max(
                    -1.0,
                    min(1.0, _float(item.get("emotional_value", 0.0))),
                ),
                source_message_id,
            )
            counters["memories"] += 1

        for item in (archive.get("identity_updates") or [])[:6]:
            if not isinstance(item, dict):
                continue

            key = str(item.get("key", "")).strip()
            value = str(item.get("value", "")).strip()
            if not key or not value:
                continue

            subject = (
                "user" if item.get("subject") == "user" else "eva"
            )
            confidence = _clamp(item.get("confidence", 0.75))
            self.store.upsert_identity(
                subject,
                key[:80],
                value[:1000],
                confidence,
            )
            self.remember(
                "identity",
                f"{subject}.{key}: {value}"[:2000],
                max(0.82, confidence),
                0.1,
                source_message_id,
            )

        for item in (archive.get("entities") or [])[:12]:
            if not isinstance(item, dict):
                continue
            entity_id = self.upsert_entity(
                item.get("name"),
                item.get("type", "other"),
                item.get("summary", ""),
                item.get("importance", 0.5),
            )
            if entity_id:
                counters["entities"] += 1

        for item in (archive.get("relations") or [])[:12]:
            if not isinstance(item, dict):
                continue
            self.link_entities(
                item.get("source"),
                item.get("relation"),
                item.get("target"),
                item.get("confidence", 0.7),
                None,
            )

        for item in (archive.get("goals") or [])[:4]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            goal_id = self.store.add_goal(
                title[:180],
                str(item.get("description", ""))[:1200],
                item.get("priority", 0.5),
            )
            if goal_id:
                counters["goals"] += 1

        if counters["memories"] or counters["entities"]:
            self.rebuild_memory_tree()

        return counters

    def cognitive_context(self, user_message):
        return {
            "identity": self.store.get_identity(),
            "relationship": self.store.get_relationship(),
            "memories": self.recall(user_message),
            "entities": self.find_entities(user_message),
            "memory_tree": self.get_memory_tree(8),
            "goals": self.store.get_active_goals(),
            "tasks": self.get_tasks(8),
            "emotion": self.store.latest_emotional_state(),
        }

    def status(self):
        return {
            "engine": "memory-cortex-v0.4",
            "embeddings": self.embedder.status(),
            "tree_branches": len(self.get_memory_tree(50)),
            "entities": len(self.list_entities(100)),
            "tasks": len(self.get_tasks(100)),
        }
