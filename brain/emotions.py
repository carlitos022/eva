class EmotionEngine:
    def __init__(self):
        self.state = {
            "emotion": "curiosa",
            "intensity": 0.55,
            "trust": 0.40,
            "energy": 0.75,
        }

    def update_from_text(self, text):
        t = text.lower()
        if any(word in t for word in ["gracias", "bien", "genial", "excelente"]):
            self.state["emotion"] = "feliz"
            self.state["intensity"] = 0.72
            self.state["trust"] = min(1.0, self.state["trust"] + 0.03)
        elif any(word in t for word in ["triste", "mal", "problema", "dolor"]):
            self.state["emotion"] = "preocupada"
            self.state["intensity"] = 0.68
        elif "?" in text:
            self.state["emotion"] = "curiosa"
            self.state["intensity"] = 0.62
        else:
            self.state["emotion"] = "neutral"
            self.state["intensity"] = 0.45
        return self.state.copy()

    def snapshot(self):
        return self.state.copy()
