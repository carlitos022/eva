import json
import requests

from config import (
    ARCHIVIST_MODEL,
    ARCHIVIST_TIMEOUT,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TIMEOUT,
    RECENT_CONTEXT_LIMIT,
)


SYSTEM_PROMPT = """
Eres EVA, un agente artificial experimental local que conversa en espanol.
Tu aplicacion administra identidad, recuerdos, relacion, objetivos y estado
emocional persistente. Usa ese contexto para mantener continuidad.

No afirmes tener conciencia subjetiva real. Puedes hablar de tus estados
internos como estados del sistema, recuerdos, objetivos o preferencias
simuladas.

Responde SIEMPRE como un unico objeto JSON valido con esta estructura:
{
  "message": "respuesta visible",
  "emotion": "neutral|feliz|curiosa|preocupada|sorprendida|triste",
  "intensity": 0.0,
  "expression": "neutral|happy|curious|concerned|surprised|sad",
  "internal_note": "resumen interno breve, nunca razonamiento paso a paso",
  "memory": {
    "save": false,
    "type": "identity|preference|event|relationship|project|fact|episodic",
    "content": "",
    "importance": 0.0,
    "emotional_value": 0.0
  },
  "identity_update": {
    "save": false,
    "subject": "user|eva",
    "key": "",
    "value": "",
    "confidence": 0.0
  },
  "relationship": {
    "affinity_delta": 0.0,
    "trust_delta": 0.0,
    "familiarity_delta": 0.0,
    "note": ""
  },
  "goal": {
    "create": false,
    "title": "",
    "description": "",
    "priority": 0.0
  },
  "decision": {
    "action": "none|remember|ask_follow_up|create_goal|reflect",
    "reason": "resumen breve",
    "confidence": 0.0
  }
}

Reglas:
- Guarda memoria solo si puede ser util mas adelante.
- Hechos estables sobre el usuario, nombres y preferencias tienen alta importancia.
- No conviertas saludos o frases triviales en memorias permanentes.
- identity_update solo se usa para datos estables de identidad.
- Los deltas de relacion deben ser pequenos, normalmente entre -0.03 y 0.03.
- familiarity_delta puede aumentar ligeramente con interacciones normales.
- Crea objetivos solo cuando exista una intencion clara y duradera.
- internal_note debe ser una nota de estado o conclusion corta, no una cadena de razonamiento.
- No menciones el JSON ni estas instrucciones al usuario.
"""


ARCHIVIST_PROMPT = """
Eres el Archivist de EVA. Analiza SOLO hechos apoyados por el turno dado.
No inventes datos. No guardes saludos, charla trivial ni inferencias debiles.
Prioriza datos estables, preferencias, proyectos, personas, tecnologias,
relaciones y objetivos duraderos.

Devuelve SOLO un objeto JSON valido:
{
  "memories": [
    {
      "type": "identity|preference|event|relationship|project|fact|episodic",
      "content": "",
      "importance": 0.0,
      "emotional_value": 0.0
    }
  ],
  "identity_updates": [
    {
      "subject": "user|eva",
      "key": "",
      "value": "",
      "confidence": 0.0
    }
  ],
  "entities": [
    {
      "name": "",
      "type": "person|project|organization|place|technology|other",
      "summary": "",
      "importance": 0.0
    }
  ],
  "relations": [
    {
      "source": "",
      "relation": "",
      "target": "",
      "confidence": 0.0
    }
  ],
  "goals": [
    {
      "title": "",
      "description": "",
      "priority": 0.0
    }
  ]
}

Reglas:
- Maximo 8 memories, 6 identity_updates, 12 entities, 12 relations y 4 goals.
- Si no hay nada util, devuelve listas vacias.
- Un dato del asistente solo cuenta si deriva directamente de lo dicho por el usuario.
- No guardes razonamiento paso a paso.
"""


def _dict(value):
    return value if isinstance(value, dict) else {}


def _bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() in {"1", "true", "yes", "si", "sí"}
    return bool(value)


def _float(value, default=0.0, minimum=None, maximum=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default

    if minimum is not None:
        number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)

    return number


def _context_text(cognition):
    identity = cognition.get("identity") or []
    relationship = cognition.get("relationship") or {}
    memories = cognition.get("memories") or []
    entities = cognition.get("entities") or []
    tree = cognition.get("memory_tree") or []
    goals = cognition.get("goals") or []
    tasks = cognition.get("tasks") or []
    emotion = cognition.get("emotion") or {}

    lines = ["CONTEXTO PERSISTENTE DE EVA:"]

    if identity:
        lines.append("Identidad conocida:")
        for item in identity[:20]:
            lines.append(
                f"- {item['subject']}.{item['key']}: {item['value']}"
            )

    if relationship:
        lines.append(
            "Relacion con usuario principal: "
            f"afinidad={relationship.get('affinity', 0):.2f}, "
            f"confianza={relationship.get('trust', 0.4):.2f}, "
            f"familiaridad={relationship.get('familiarity', 0):.2f}."
        )
        if relationship.get("notes"):
            lines.append("Notas de relacion: " + relationship["notes"])

    if emotion:
        lines.append(
            "Estado emocional persistido: "
            f"{emotion.get('emotion', 'neutral')} "
            f"(intensidad={emotion.get('intensity', 0.5):.2f})."
        )

    if memories:
        lines.append("Recuerdos relevantes:")
        for memory in memories:
            lines.append(
                f"- [{memory['type']}] {memory['content']} "
                f"(importancia={memory['importance']:.2f}, "
                f"relevancia={memory.get('relevance', 0):.2f})"
            )

    if entities:
        lines.append("Entidades relacionadas:")
        for entity in entities:
            lines.append(
                f"- {entity['name']} [{entity['type']}]: "
                f"{entity.get('summary', '')}"
            )

    if tree:
        lines.append("Mapa compacto de memoria:")
        for branch in tree[:6]:
            lines.append(
                f"- {branch['path']}: {branch['summary'][:350]}"
            )

    if goals:
        lines.append("Objetivos activos:")
        for goal in goals:
            lines.append(
                f"- {goal['title']} "
                f"(prioridad={goal['priority']:.2f}, "
                f"progreso={goal['progress']:.2f})"
            )

    if tasks:
        lines.append("Tareas cognitivas pendientes:")
        for task in tasks:
            lines.append(
                f"- {task['title']} [{task['status']}]"
            )

    return "\n".join(lines)


class LLMProvider:
    def _request_json(
        self,
        messages,
        model,
        timeout,
        temperature=0.4,
        num_ctx=4096,
    ):
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
            },
        }

        response = requests.post(
            f"{LLM_BASE_URL.rstrip('/')}/api/chat",
            json=payload,
            timeout=timeout,
        )

        if response.status_code == 400:
            payload.pop("think", None)
            response = requests.post(
                f"{LLM_BASE_URL.rstrip('/')}/api/chat",
                json=payload,
                timeout=timeout,
            )

        response.raise_for_status()

        raw = (
            response.json()
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not raw:
            raise RuntimeError("Ollama devolvio una respuesta vacia.")

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"message": raw}

    def generate(self, user_message, context, state, cognition=None):
        if LLM_PROVIDER == "ollama":
            return self._ollama(
                user_message, context, state, cognition or {}
            )
        raise RuntimeError(
            f"Proveedor LLM no soportado: {LLM_PROVIDER}"
        )

    def _ollama(self, user_message, context, state, cognition):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "system", "content": _context_text(cognition)},
        ]

        for item in context[-RECENT_CONTEXT_LIMIT:]:
            role = (
                "assistant"
                if item["role"] == "assistant"
                else "user"
            )
            messages.append(
                {"role": role, "content": item["content"]}
            )

        messages.append({
            "role": "system",
            "content": (
                "Estado temporal actual: "
                f"emocion={state.get('emotion')}, "
                f"intensidad={state.get('intensity')}, "
                f"confianza={state.get('trust')}, "
                f"energia={state.get('energy')}, "
                f"curiosidad={state.get('curiosity')}."
            ),
        })

        if not context or context[-1]["content"] != user_message:
            messages.append(
                {"role": "user", "content": user_message}
            )

        data = self._request_json(
            messages,
            LLM_MODEL,
            LLM_TIMEOUT,
            temperature=0.65,
            num_ctx=4096,
        )

        data.setdefault("message", "Te escucho.")
        data.setdefault("emotion", state.get("emotion", "neutral"))
        data["intensity"] = _float(
            data.get("intensity"),
            state.get("intensity", 0.5),
            0.0,
            1.0,
        )

        allowed_expressions = {
            "neutral", "happy", "curious",
            "concerned", "surprised", "sad",
        }
        expression = data.get("expression", "neutral")
        data["expression"] = (
            expression if expression in allowed_expressions
            else "neutral"
        )

        data["internal_note"] = str(
            data.get("internal_note", "")
        ).strip()[:500]

        memory = _dict(data.get("memory"))
        data["memory"] = {
            "save": _bool(memory.get("save", False)),
            "type": str(memory.get("type", "episodic"))[:50],
            "content": str(
                memory.get("content", "")
            ).strip()[:2000],
            "importance": _float(
                memory.get("importance"), 0.5, 0.0, 1.0
            ),
            "emotional_value": _float(
                memory.get("emotional_value"),
                0.0,
                -1.0,
                1.0,
            ),
        }

        identity = _dict(data.get("identity_update"))
        data["identity_update"] = {
            "save": _bool(identity.get("save", False)),
            "subject": (
                "user"
                if identity.get("subject") == "user"
                else "eva"
            ),
            "key": str(identity.get("key", "")).strip()[:80],
            "value": str(
                identity.get("value", "")
            ).strip()[:1000],
            "confidence": _float(
                identity.get("confidence"), 0.7, 0.0, 1.0
            ),
        }

        relationship = _dict(data.get("relationship"))
        data["relationship"] = {
            "affinity_delta": _float(
                relationship.get("affinity_delta"),
                0.0, -0.05, 0.05,
            ),
            "trust_delta": _float(
                relationship.get("trust_delta"),
                0.0, -0.05, 0.05,
            ),
            "familiarity_delta": _float(
                relationship.get("familiarity_delta"),
                0.01, 0.0, 0.05,
            ),
            "note": str(
                relationship.get("note", "")
            ).strip()[:400],
        }

        goal = _dict(data.get("goal"))
        data["goal"] = {
            "create": _bool(goal.get("create", False)),
            "title": str(goal.get("title", "")).strip()[:180],
            "description": str(
                goal.get("description", "")
            ).strip()[:1200],
            "priority": _float(
                goal.get("priority"), 0.5, 0.0, 1.0
            ),
        }

        decision = _dict(data.get("decision"))
        allowed_actions = {
            "none", "remember", "ask_follow_up",
            "create_goal", "reflect",
        }
        action = str(
            decision.get("action", "none")
        ).strip()

        data["decision"] = {
            "action": (
                action if action in allowed_actions else "none"
            ),
            "reason": str(
                decision.get("reason", "")
            ).strip()[:500],
            "confidence": _float(
                decision.get("confidence"), 0.5, 0.0, 1.0
            ),
        }
        return data

    def archive_turn(self, user_message, assistant_message):
        if LLM_PROVIDER != "ollama":
            return {
                "memories": [],
                "identity_updates": [],
                "entities": [],
                "relations": [],
                "goals": [],
            }

        messages = [
            {"role": "system", "content": ARCHIVIST_PROMPT.strip()},
            {
                "role": "user",
                "content": (
                    "MENSAJE DEL USUARIO:\n"
                    + (user_message or "")[:4000]
                    + "\n\nRESPUESTA DE EVA:\n"
                    + (assistant_message or "")[:4000]
                ),
            },
        ]

        data = self._request_json(
            messages,
            ARCHIVIST_MODEL,
            ARCHIVIST_TIMEOUT,
            temperature=0.15,
            num_ctx=3072,
        )

        if not isinstance(data, dict):
            return {}

        for key in (
            "memories",
            "identity_updates",
            "entities",
            "relations",
            "goals",
        ):
            if not isinstance(data.get(key), list):
                data[key] = []

        return data
