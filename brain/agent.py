from brain.memory import MemoryStore
from brain.emotions import EmotionEngine
from brain.llm import LLMProvider

from config import RECENT_CONTEXT_LIMIT, MEMORY_MIN_IMPORTANCE


class EvaAgent:
    def __init__(self):
        self.memory = MemoryStore()
        self.emotions = EmotionEngine()
        self.llm = LLMProvider()

    def initialize(self):
        self.memory.initialize()

        persisted_emotion = self.memory.latest_emotional_state()

        if persisted_emotion:
            self.emotions.restore(persisted_emotion)
        else:
            self.memory.save_emotional_state(
                self.emotions.snapshot()
            )

    def get_state(self):
        return {
            "name": "EVA",
            **self.emotions.snapshot(),
            "memory": self.memory.recent(6),
            "identity": self.memory.get_identity(),
            "relationship": self.memory.get_relationship(),
            "goals": self.memory.get_active_goals(),
            "stats": self.memory.stats()
        }

    def _persist_cognition(
        self,
        result,
        user_message_id,
        state
    ):
        memory = result.get("memory") or {}

        if (
            memory.get("save")
            and memory.get("content")
            and float(memory.get("importance", 0.0))
            >= MEMORY_MIN_IMPORTANCE
        ):
            self.memory.add_memory(
                memory.get("type", "episodic"),
                memory["content"],
                memory.get("importance", 0.5),
                memory.get("emotional_value", 0.0),
                user_message_id
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
                identity.get("confidence", 0.8)
            )

            self.memory.add_memory(
                "identity",
                (
                    f"{identity.get('subject', 'user')}: "
                    f"{identity['key']} = {identity['value']}"
                ),
                max(
                    0.85,
                    float(identity.get("confidence", 0.8))
                ),
                0.1,
                user_message_id
            )

        relationship = result.get("relationship") or {}

        self.memory.update_relationship(
            "usuario_principal",
            relationship.get("affinity_delta", 0.0),
            relationship.get("trust_delta", 0.0),
            relationship.get("familiarity_delta", 0.01),
            relationship.get("note", "")
        )

        goal = result.get("goal") or {}

        if goal.get("create") and goal.get("title"):
            self.memory.add_goal(
                goal["title"],
                goal.get("description", ""),
                goal.get("priority", 0.5)
            )

        internal_note = result.get("internal_note", "")

        if internal_note:
            self.memory.log_internal_event(
                "reflection",
                internal_note,
                max(
                    0.4,
                    float(result.get("intensity", 0.5))
                )
            )

        decision = result.get("decision") or {}

        self.memory.save_decision(
            decision.get("action", "none"),
            decision.get("reason", ""),
            decision.get("confidence", 0.5)
        )

        self.memory.save_emotional_state(state)

    def respond(self, user_message):
        user_message_id = self.memory.add(
            "user",
            user_message
        )

        heuristic_state = self.emotions.update_from_text(
            user_message
        )

        context = self.memory.recent(
            RECENT_CONTEXT_LIMIT
        )

        cognition = self.memory.cognitive_context(
            user_message
        )

        result = self.llm.generate(
            user_message,
            context,
            heuristic_state,
            cognition
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
            )
        )

        answer = result["message"]
        self.memory.add("assistant", answer)

        self._persist_cognition(
            result,
            user_message_id,
            state
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
            "decision": (
                (result.get("decision") or {})
                .get("action", "none")
            )
        }
