import math
import time

import requests

from config import (
    EMBEDDINGS_ENABLED,
    EMBEDDING_MODEL,
    EMBEDDING_TIMEOUT,
    EMBEDDING_RETRY_SECONDS,
    LLM_BASE_URL,
)


class OllamaEmbeddingClient:
    """Embeddings locales con degradacion automatica a memoria lexical."""

    def __init__(self):
        self.enabled = EMBEDDINGS_ENABLED
        self.model = EMBEDDING_MODEL
        self.last_error = ""
        self.last_success_at = None
        self._disabled_until = 0.0

    def _available_now(self):
        return self.enabled and time.time() >= self._disabled_until

    def embed(self, text):
        text = (text or "").strip()
        if not text or not self._available_now():
            return None

        base = LLM_BASE_URL.rstrip("/")

        try:
            response = requests.post(
                f"{base}/api/embed",
                json={"model": self.model, "input": text},
                timeout=EMBEDDING_TIMEOUT,
            )

            if response.ok:
                vectors = response.json().get("embeddings") or []
                if vectors and isinstance(vectors[0], list):
                    self.last_error = ""
                    self.last_success_at = time.time()
                    return [float(value) for value in vectors[0]]

            # Compatibilidad con versiones antiguas de Ollama.
            response = requests.post(
                f"{base}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=EMBEDDING_TIMEOUT,
            )
            response.raise_for_status()

            vector = response.json().get("embedding")
            if isinstance(vector, list) and vector:
                self.last_error = ""
                self.last_success_at = time.time()
                return [float(value) for value in vector]

            raise RuntimeError("Ollama no devolvio un embedding valido.")

        except Exception as exc:
            self.last_error = str(exc)
            self._disabled_until = time.time() + max(
                5, EMBEDDING_RETRY_SECONDS
            )
            return None

    @staticmethod
    def cosine(left, right):
        if not left or not right or len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))

        if left_norm <= 0.0 or right_norm <= 0.0:
            return 0.0

        return max(-1.0, min(1.0, dot / (left_norm * right_norm)))

    def status(self):
        return {
            "enabled": self.enabled,
            "model": self.model,
            "ready": bool(self.last_success_at),
            "last_error": self.last_error,
            "retry_in_seconds": max(
                0, int(self._disabled_until - time.time())
            ),
        }
