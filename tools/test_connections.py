import os
import sys

# Permite ejecutar este archivo directamente con:
# python tools\test_connections.py
# agregando la raiz del proyecto al path de Python.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import requests
import mysql.connector

from config import (
    LLM_BASE_URL, LLM_MODEL,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_CONNECT_TIMEOUT
)


def test_ollama():
    print("=== OLLAMA ===")
    try:
        r = requests.get(f"{LLM_BASE_URL.rstrip('/')}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m.get("name", "") for m in r.json().get("models", [])]
        print("Servidor:", LLM_BASE_URL)
        print("Modelo esperado:", LLM_MODEL)
        print("Modelos encontrados:", ", ".join(models) or "(ninguno)")
        if not any(name == LLM_MODEL or name.startswith(LLM_MODEL + ":") for name in models):
            print("AVISO: Ollama responde, pero el modelo esperado no aparece en la lista.")
            return False
        print("OK: Ollama responde y el modelo esta disponible.")
        return True
    except Exception as exc:
        print("ERROR OLLAMA:", exc)
        print("SUGERENCIA: inicia Ollama con 'ollama serve' o abre la aplicacion Ollama.")
        return False


def test_mysql():
    print("\n=== MYSQL ===")
    try:
        con = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=DB_CONNECT_TIMEOUT,
            charset="utf8mb4"
        )
        cur = con.cursor()
        cur.execute("SELECT VERSION(), DATABASE(), CURRENT_USER()")
        version, database, current_user = cur.fetchone()
        print("Servidor:", f"{DB_HOST}:{DB_PORT}")
        print("Version:", version)
        print("Base:", database)
        print("Usuario:", current_user)
        print("OK: MySQL conectado.")
        cur.close()
        con.close()
        return True
    except Exception as exc:
        print("ERROR MYSQL:", exc)
        return False


if __name__ == "__main__":
    ollama_ok = test_ollama()
    mysql_ok = test_mysql()

    print("\n=== RESULTADO ===")
    print("Ollama:", "OK" if ollama_ok else "FALLO")
    print("MySQL :", "OK" if mysql_ok else "FALLO")

    if not (ollama_ok and mysql_ok):
        sys.exit(1)

    print("\nTodo listo para iniciar EVA.")
