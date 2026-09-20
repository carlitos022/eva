from brain.archivist import PostTurnArchivist
from brain.events import EventBus
from brain.heartbeat import HeartbeatEngine
from brain.memory import MemoryStore
from brain.memory_cortex import MemoryCortex
from brain.emotions import EmotionEngine
from brain.llm import LLMProvider

from config import (
    ARCHIVIST_ENABLED,
    MEMORY_MIN_IMPORTANCE,
    RECENT_CONTEXT_LIMIT,
)


class EvaAgent:
    def __init__(self):
        self.memory = MemoryStore()
        self.cortex = MemoryCortex(self.memory)
        self.emotions = EmotionEngine()
        self.llm = LLMProvider()
        self.events = EventBus()
        self.archivist = PostTurnArchivist(
            self.cortex,
            self.llm,
            self.events,
        )
        self.heartbeat = HeartbeatEngine(
            self.cortex,
            self.events,
        )

    def initialize(self):
        self.memory.initialize()
        self.cortex.initialize()

        persisted_emotion = self.memory.latest_emotional_state()

        if persisted_emotion:
            self.emotions.restore(persisted_emotion)
        else:
            self.memory.save_emotional_state(
                self.emotions.snapshot()
            )

        self.heartbeat.start()

    def get_state(self):
        return {
            "name": "EVA",
            **self.emotions.snapshot(),
            "memory": self.memory.recent(6),
            "identity": self.memory.get_identity(),
            "relationship": self.memory.get_relationship(),
            "goals": self.memory.get_active_goals(),
            "tasks": self.cortex.get_tasks(),
            "entities": self.cortex.list_entities(20),
            "memory_tree": self.cortex.get_memory_tree(12),
            "stats": self.memory.stats(),
            "memory_cortex": self.cortex.status(),
            "archivist": self.archivist.status(),
            "heartbeat": self.heartbeat.status(),
        }

    def _persist_cognition(
        self,
        result,
        user_message_id,
        state,
    ):
        # Si el Archivist esta desactivado, mantenemos exactamente
        # el comportamiento v0.3 como fallback.
        if not ARCHIVIST_ENABLED:
            memory = result.get("memory") or {}

            if (
                memory.get("save")
                and memory.get("content")
                and float(memory.get("importance", 0.0))
                >= MEMORY_MIN_IMPORTANCE
            ):
                self.cortex.remember(
                    memory.get("type", "episodic"),
                    memory["content"],
                    memory.get("importance", 0.5),
                    memory.get("emotional_value", 0.0),
                    user_message_id,
                )

            identity = result.get("identity_update") or {}

            if (
                identity.get("save")
                and identity.get("key")
                and identity.get("value")
            ):
                self.memory.upsert_identity(
                    identity.get("subject", "user"),
                    identity["key"],
                    identity["value"],
                    identity.get("confidence", 0.8),
                )

                self.cortex.remember(
                    "identity",
                    (
                        f"{identity.get('subject', 'user')}: "
                        f"{identity['key']} = {identity['value']}"
                    ),
                    max(
                        0.85,
                        float(identity.get("confidence", 0.8)),
                    ),
                    0.1,
                    user_message_id,
                )

            goal = result.get("goal") or {}

            if goal.get("create") and goal.get("title"):
                self.memory.add_goal(
                    goal["title"],
                    goal.get("description", ""),
                    goal.get("priority", 0.5),
                )

        relationship = result.get("relationship") or {}

        self.memory.update_relationship(
            "usuario_principal",
            relationship.get("affinity_delta", 0.0),
            relationship.get("trust_delta", 0.0),
            relationship.get("familiarity_delta", 0.01),
            relationship.get("note", ""),
        )

        internal_note = result.get("internal_note", "")

        if internal_note:
            self.memory.log_internal_event(
                "reflection",
                internal_note,
                max(
                    0.4,
                    float(result.get("intensity", 0.5)),
                ),
            )

        decision = result.get("decision") or {}

        self.memory.save_decision(
            decision.get("action", "none"),
            decision.get("reason", ""),
            decision.get("confidence", 0.5),
        )

        self.memory.save_emotional_state(state)

    def respond(self, user_message):
        user_message_id = self.memory.add(
            "user",
            user_message,
        )

        self.events.publish(
            "user_message",
            {
                "message_id": user_message_id,
                "content": user_message,
            },
        )

        heuristic_state = self.emotions.update_from_text(
            user_message
        )

        context = self.memory.recent(
            RECENT_CONTEXT_LIMIT
        )

        cognition = self.cortex.cognitive_context(
            user_message
        )

        result = self.llm.generate(
            user_message,
            context,
            heuristic_state,
            cognition,
        )

        relationship = result.get("relationship") or {}

        state = self.emotions.apply_llm_state(
            result.get("emotion"),
            result.get("intensity"),
            relationship.get("trust_delta", 0.0),
            (
                0.01
                if result.get("emotion") == "curiosa"
                else 0.0
            ),
        )

        answer = result["message"]
        assistant_message_id = self.memory.add(
            "assistant",
            answer,
        )

        self._persist_cognition(
            result,
            user_message_id,
            state,
        )

        archivist_queued = self.archivist.submit(
            user_message,
            answer,
            user_message_id,
        )

        self.events.publish(
            "assistant_message",
            {
                "message_id": assistant_message_id,
                "content": answer,
                "emotion": state["emotion"],
            },
        )

        expression = result.get("expression") or {
            "feliz": "happy",
            "curiosa": "curious",
            "preocupada": "concerned",
            "sorprendida": "surprised",
            "triste": "sad",
            "neutral": "neutral",
        }.get(state["emotion"], "neutral")

        return {
            "message": answer,
            "emotion": state["emotion"],
            "intensity": state["intensity"],
            "expression": expression,
            "memory_saved": bool(
                (result.get("memory") or {}).get("save")
            ),
            "archivist_queued": archivist_queued,
            "decision": (
                (result.get("decision") or {})
                .get("action", "none")
            ),
        }
