class EmotionEngine:
    def __init__(self):
        self.state = {
            "emotion": "curiosa",
            "intensity": 0.55,
            "trust": 0.40,
            "energy": 0.75,
        }

    def update_from_text(self, text):
        # Heuristica inicial. El LLM refina el estado despues.
        t = text.lower()

        if any(word in t for word in ["gracias", "bien", "genial", "excelente", "feliz", "contento"]):
            self.state["emotion"] = "feliz"
            self.state["intensity"] = 0.72
            self.state["trust"] = min(1.0, self.state["trust"] + 0.03)

        elif any(word in t for word in ["triste", "llorar", "perdida", "perdi", "pena"]):
            self.state["emotion"] = "triste"
            self.state["intensity"] = 0.70

        elif any(word in t for word in ["mal", "problema", "dolor", "preocupado", "preocupada"]):
            self.state["emotion"] = "preocupada"
            self.state["intensity"] = 0.68

        elif any(word in t for word in ["sorpresa", "sorprendente", "increible"]):
            self.state["emotion"] = "sorprendida"
            self.state["intensity"] = 0.72

        elif "?" in text:
            self.state["emotion"] = "curiosa"
            self.state["intensity"] = 0.62

        else:
            self.state["emotion"] = "neutral"
            self.state["intensity"] = 0.45

        return self.state.copy()

    def apply_llm_state(self, emotion, intensity):
        allowed = {
            "neutral",
            "feliz",
            "curiosa",
            "preocupada",
            "sorprendida",
            "triste"
        }

        if emotion in allowed:
            self.state["emotion"] = emotion

        try:
            self.state["intensity"] = max(0.0, min(1.0, float(intensity)))
        except (TypeError, ValueError):
            pass

        return self.state.copy()

    def snapshot(self):
        return self.state.copy()
