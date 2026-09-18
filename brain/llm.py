from config import LLM_PROVIDER

class LLMProvider:
    def generate(self, user_message, context, state):
        if LLM_PROVIDER == "demo":
            return self._demo(user_message, state)

        raise RuntimeError(
            "El proveedor LLM aun no esta configurado. "
            "Usa EVA_LLM_PROVIDER=demo para la v0.1."
        )

    def _demo(self, user_message, state):
        emotion = state.get("emotion", "neutral")
        lowered = user_message.lower()

        if any(x in lowered for x in ["hola", "buenas", "hey"]):
            reply = "Hola. Soy EVA. Esta es mi primera version y estoy aprendiendo a mantener una identidad y recuerdos."
        elif "quien eres" in lowered or "quién eres" in lowered:
            reply = "Soy EVA, un agente artificial experimental. Mi identidad, memoria y estado emocional viven fuera del modelo de lenguaje."
        elif "recuerdas" in lowered:
            reply = "Guardo nuestra conversacion en una memoria SQLite. Todavia es una memoria sencilla, pero persistira cuando cierres el programa."
        else:
            reply = f"Te escucho. En este momento mi estado es {emotion}. La v0.1 ya puede conversar, recordar y cambiar su expresion."

        return {
            "thought": "Debo responder de forma coherente con mi estado y conservar esta experiencia.",
            "message": reply
        }
