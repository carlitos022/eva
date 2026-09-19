class EmotionEngine:
    def __init__(self):
        self.state = {
            "emotion": "curiosa",
            "intensity": 0.55,
            "trust": 0.40,
            "energy": 0.75,
            "curiosity": 0.65,
        }

    def restore(self, saved_state):
        if not saved_state:
            return self.snapshot()

        for key in ["emotion", "intensity", "trust", "energy", "curiosity"]:
            if key in saved_state and saved_state[key] is not None:
                self.state[key] = saved_state[key]

        return self.snapshot()

    def update_from_text(self, text):
        t = text.lower()

        if any(word in t for word in [
            "gracias", "bien", "genial", "excelente", "feliz", "contento"
        ]):
            self.state["emotion"] = "feliz"
            self.state["intensity"] = 0.72
            self.state["trust"] = min(1.0, self.state["trust"] + 0.02)

        elif any(word in t for word in [
            "triste", "llorar", "perdida", "perdi", "pena"
        ]):
            self.state["emotion"] = "triste"
            self.state["intensity"] = 0.70

        elif any(word in t for word in [
            "mal", "problema", "dolor", "preocupado", "preocupada"
        ]):
            self.state["emotion"] = "preocupada"
            self.state["intensity"] = 0.68

        elif any(word in t for word in [
            "sorpresa", "sorprendente", "increible"
        ]):
            self.state["emotion"] = "sorprendida"
            self.state["intensity"] = 0.72
            self.state["curiosity"] = min(
                1.0, self.state["curiosity"] + 0.05
            )

        elif "?" in text:
            self.state["emotion"] = "curiosa"
            self.state["intensity"] = 0.62
            self.state["curiosity"] = min(
                1.0, self.state["curiosity"] + 0.02
            )

        else:
            self.state["emotion"] = "neutral"
            self.state["intensity"] = 0.45

        self.state["energy"] = max(
            0.25, min(1.0, self.state["energy"] - 0.002)
        )

        return self.state.copy()

    def apply_llm_state(
        self,
        emotion,
        intensity,
        trust_delta=0.0,
        curiosity_delta=0.0
    ):
        allowed = {
            "neutral", "feliz", "curiosa", "preocupada",
            "sorprendida", "triste"
        }

        if emotion in allowed:
            self.state["emotion"] = emotion

        try:
            self.state["intensity"] = max(
                0.0, min(1.0, float(intensity))
            )
        except (TypeError, ValueError):
            pass

        try:
            self.state["trust"] = max(
                0.0,
                min(1.0, self.state["trust"] + float(trust_delta))
            )
        except (TypeError, ValueError):
            pass

        try:
            self.state["curiosity"] = max(
                0.0,
                min(
                    1.0,
                    self.state["curiosity"] + float(curiosity_delta)
                )
            )
        except (TypeError, ValueError):
            pass

        return self.state.copy()

    def snapshot(self):
        return self.state.copy()
