import os

APP_NAME = "EVA"
APP_VERSION = "0.1-demo"
HOST = "127.0.0.1"
PORT = 5000
DEBUG = True

LLM_PROVIDER = os.getenv("EVA_LLM_PROVIDER", "demo")
LLM_BASE_URL = os.getenv("EVA_LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("EVA_LLM_API_KEY", "")
LLM_MODEL = os.getenv("EVA_LLM_MODEL", "")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "eva.db")
