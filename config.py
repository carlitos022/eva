import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "EVA"
APP_VERSION = "0.1.1"
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
DB_HOST = os.getenv("EVA_DB_HOST", "209.126.77.129")
DB_PORT = int(os.getenv("EVA_DB_PORT", "3306"))
DB_NAME = os.getenv("EVA_DB_NAME", "eva_ai")
DB_USER = os.getenv("EVA_DB_USER", "eva_user")
DB_PASSWORD = os.getenv("EVA_DB_PASSWORD", "")
DB_CONNECT_TIMEOUT = int(os.getenv("EVA_DB_CONNECT_TIMEOUT", "10"))

# SQLite queda como fallback de emergencia
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "eva.db")
