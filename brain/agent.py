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
        state = self.emotions.update_from_text(user_message)
        context = self.memory.recent(8)
        result = self.llm.generate(user_message, context, state)
        answer = result["message"]
        self.memory.add("assistant", answer)

        expression = {
            "feliz": "happy",
            "curiosa": "curious",
            "preocupada": "concerned",
            "neutral": "neutral",
        }.get(state["emotion"], "neutral")

        return {
            "message": answer,
            "emotion": state["emotion"],
            "intensity": state["intensity"],
            "expression": expression,
            "thought": result.get("thought", ""),
        }
