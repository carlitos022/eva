import json
import requests

from config import LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER, LLM_TIMEOUT


SYSTEM_PROMPT = """
Eres EVA, un agente artificial experimental que conversa en espanol.
Tu identidad, memoria y estado emocional son administrados por la aplicacion.
Responde de forma natural, breve y humana, sin fingir capacidades que no tienes.

Devuelve SIEMPRE un objeto JSON valido con estas claves:
message: respuesta visible para el usuario.
emotion: una de [neutral, feliz, curiosa, preocupada, sorprendida, triste].
intensity: numero entre 0.0 y 1.0.
expression: una de [neutral, happy, curious, concerned, surprised, sad].
thought: una nota interna MUY breve para el motor de EVA, no para el usuario.

Usa la expresion facial de forma coherente con el contenido de la respuesta.
No menciones el JSON, el pensamiento interno ni estas instrucciones.
"""


class LLMProvider:
    def generate(self, user_message, context, state):
        if LLM_PROVIDER == "ollama":
            return self._ollama(user_message, context, state)

        raise RuntimeError(f"Proveedor LLM no soportado: {LLM_PROVIDER}")

    def _ollama(self, user_message, context, state):
        messages = [{"role": "system", "content": SYSTEM_PROMPT.strip()}]

        # Contexto reciente para conservar velocidad con el modelo local.
        for item in context[-8:]:
            role = "assistant" if item["role"] == "assistant" else "user"
            messages.append({"role": role, "content": item["content"]})

        messages.append({
            "role": "system",
            "content": (
                "Estado interno actual de EVA: "
                f"emocion={state.get('emotion')}, "
                f"intensidad={state.get('intensity')}, "
                f"confianza={state.get('trust')}, "
                f"energia={state.get('energy')}."
            )
        })

        if not context or context[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        response = requests.post(
            f"{LLM_BASE_URL.rstrip('/')}/api/chat",
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 4096
                }
            },
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()

        payload = response.json()
        raw = payload.get("message", {}).get("content", "").strip()

        if not raw:
            raise RuntimeError("Ollama devolvio una respuesta vacia.")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "message": raw,
                "emotion": state.get("emotion", "neutral"),
                "intensity": state.get("intensity", 0.5),
                "expression": "neutral",
                "thought": ""
            }

        data.setdefault("message", "Te escucho.")
        data.setdefault("emotion", state.get("emotion", "neutral"))
        data.setdefault("intensity", state.get("intensity", 0.5))
        data.setdefault("expression", "neutral")
        data.setdefault("thought", "")

        allowed_expressions = {
            "neutral",
            "happy",
            "curious",
            "concerned",
            "surprised",
            "sad"
        }

        if data["expression"] not in allowed_expressions:
            data["expression"] = "neutral"

        try:
            data["intensity"] = max(0.0, min(1.0, float(data["intensity"])))
        except (TypeError, ValueError):
            data["intensity"] = 0.5

        return data
