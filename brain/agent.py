from brain.memory import MemoryStore
from brain.emotions import EmotionEngine
from brain.llm import LLMProvider


class EvaAgent:
    def __init__(self):
        self.memory = MemoryStore()
        self.emotions = EmotionEngine()
        self.llm = LLMProvider()

    def initialize(self):
        self.memory.initialize()

    def get_state(self):
        return {
            "name": "EVA",
            **self.emotions.snapshot(),
            "memory": self.memory.recent(6),
        }

    def respond(self, user_message):
        self.memory.add("user", user_message)

        heuristic_state = self.emotions.update_from_text(user_message)
        context = self.memory.recent(8)
        result = self.llm.generate(user_message, context, heuristic_state)

        state = self.emotions.apply_llm_state(
            result.get("emotion"),
            result.get("intensity")
        )

        answer = result["message"]
        self.memory.add("assistant", answer)

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
            "thought": result.get("thought", ""),
        }
