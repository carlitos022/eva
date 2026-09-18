import sys
import requests
import mysql.connector

from config import (
    LLM_BASE_URL, LLM_MODEL,
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_CONNECT_TIMEOUT
)


def test_ollama():
    print("=== OLLAMA ===")
    r = requests.get(f"{LLM_BASE_URL.rstrip('/')}/api/tags", timeout=10)
    r.raise_for_status()
    models = [m.get("name", "") for m in r.json().get("models", [])]
    print("Servidor:", LLM_BASE_URL)
    print("Modelo esperado:", LLM_MODEL)
    print("Modelos encontrados:", ", ".join(models) or "(ninguno)")
    if not any(name == LLM_MODEL or name.startswith(LLM_MODEL + ":") for name in models):
        print("AVISO: el modelo esperado no aparece exactamente en la lista.")
    else:
        print("OK: Ollama responde y el modelo esta disponible.")


def test_mysql():
    print("\n=== MYSQL ===")
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


if __name__ == "__main__":
    try:
        test_ollama()
        test_mysql()
    except Exception as exc:
        print("\nERROR:", exc)
        sys.exit(1)

    print("\nTodo listo para iniciar EVA.")
