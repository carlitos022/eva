import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "EVA"
APP_VERSION = "0.4.0"
HOST = "127.0.0.1"
PORT = 5000
DEBUG = True

# LLM local via Ollama
LLM_PROVIDER = os.getenv("EVA_LLM_PROVIDER", "ollama")
LLM_BASE_URL = os.getenv("EVA_LLM_BASE_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("EVA_LLM_MODEL", "qwen3:1.7b")
LLM_TIMEOUT = int(os.getenv("EVA_LLM_TIMEOUT", "120"))

# Base de datos
DB_PROVIDER = os.getenv("EVA_DB_PROVIDER", "mysql")
DB_HOST = os.getenv("EVA_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("EVA_DB_PORT", "3306"))
DB_NAME = os.getenv("EVA_DB_NAME", "eva_ai")
DB_USER = os.getenv("EVA_DB_USER", "eva_user")
DB_PASSWORD = os.getenv("EVA_DB_PASSWORD", "")
DB_CONNECT_TIMEOUT = int(os.getenv("EVA_DB_CONNECT_TIMEOUT", "10"))

# Contexto y memoria base
RECENT_CONTEXT_LIMIT = int(os.getenv("EVA_RECENT_CONTEXT_LIMIT", "8"))
LONG_TERM_MEMORY_LIMIT = int(os.getenv("EVA_LONG_TERM_MEMORY_LIMIT", "6"))
MEMORY_SCAN_LIMIT = int(os.getenv("EVA_MEMORY_SCAN_LIMIT", "300"))
MEMORY_MIN_IMPORTANCE = float(os.getenv("EVA_MEMORY_MIN_IMPORTANCE", "0.55"))

# EVA v0.4 - Memory Cortex
EMBEDDINGS_ENABLED = os.getenv("EVA_EMBEDDINGS_ENABLED", "true").lower() in {
    "1", "true", "yes", "si"
}
EMBEDDING_MODEL = os.getenv("EVA_EMBEDDING_MODEL", "bge-m3")
EMBEDDING_TIMEOUT = int(os.getenv("EVA_EMBEDDING_TIMEOUT", "30"))
EMBEDDING_RETRY_SECONDS = int(os.getenv("EVA_EMBEDDING_RETRY_SECONDS", "60"))

ARCHIVIST_ENABLED = os.getenv("EVA_ARCHIVIST_ENABLED", "true").lower() in {
    "1", "true", "yes", "si"
}
ARCHIVIST_MODEL = os.getenv("EVA_ARCHIVIST_MODEL", LLM_MODEL)
ARCHIVIST_TIMEOUT = int(os.getenv("EVA_ARCHIVIST_TIMEOUT", str(LLM_TIMEOUT)))
ARCHIVIST_QUEUE_SIZE = int(os.getenv("EVA_ARCHIVIST_QUEUE_SIZE", "32"))
ARCHIVIST_IDLE_DELAY = float(os.getenv("EVA_ARCHIVIST_IDLE_DELAY", "0.75"))

MEMORY_TREE_REBUILD_EVERY = int(os.getenv("EVA_MEMORY_TREE_REBUILD_EVERY", "5"))

# Heartbeat preparado para la siguiente etapa autonoma.
# Permanece desactivado por defecto para no consumir recursos sin necesidad.
HEARTBEAT_ENABLED = os.getenv("EVA_HEARTBEAT_ENABLED", "false").lower() in {
    "1", "true", "yes", "si"
}
HEARTBEAT_INTERVAL = int(os.getenv("EVA_HEARTBEAT_INTERVAL", "60"))
AUTONOMY_ENABLED = os.getenv("EVA_AUTONOMY_ENABLED", "false").lower() in {
    "1", "true", "yes", "si"
}

# SQLite queda como fallback basico de emergencia
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "eva.db")
