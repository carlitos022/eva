import os
import sys

ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import requests
import mysql.connector

from brain.memory import MemoryStore
from brain.memory_cortex import MemoryCortex
from config import (
    DB_CONNECT_TIMEOUT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    EMBEDDING_MODEL,
    EMBEDDINGS_ENABLED,
    LLM_BASE_URL,
    LLM_MODEL,
)


def test_ollama():
    print("=== OLLAMA ===")

    try:
        response = requests.get(
            f"{LLM_BASE_URL.rstrip('/')}/api/tags",
            timeout=10
        )
        response.raise_for_status()

        models = [
            model.get("name", "")
            for model in response.json().get("models", [])
        ]

        print("Servidor:", LLM_BASE_URL)
        print("Modelo chat:", LLM_MODEL)
        print("Modelo embeddings:", EMBEDDING_MODEL)
        print(
            "Modelos encontrados:",
            ", ".join(models) or "(ninguno)"
        )

        chat_ok = any(
            name == LLM_MODEL
            or name.startswith(LLM_MODEL + ":")
            for name in models
        )

        embedding_ok = any(
            name == EMBEDDING_MODEL
            or name.startswith(EMBEDDING_MODEL + ":")
            for name in models
        )

        if not chat_ok:
            print(
                "ERROR: Ollama responde, pero el modelo de chat "
                "no aparece en la lista."
            )
            return False, embedding_ok

        print("OK: modelo de chat disponible.")

        if EMBEDDINGS_ENABLED:
            if embedding_ok:
                print("OK: modelo de embeddings disponible.")
            else:
                print(
                    "AVISO: bge-m3 no esta instalado. EVA seguira "
                    "funcionando con memoria lexical."
                )
                print(
                    f"Instalalo con: ollama pull {EMBEDDING_MODEL}"
                )

        return True, embedding_ok

    except Exception as exc:
        print("ERROR OLLAMA:", exc)
        print(
            "SUGERENCIA: inicia Ollama con 'ollama serve' "
            "o abre la aplicacion Ollama."
        )
        return False, False


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
        cur.execute(
            "SELECT VERSION(), DATABASE(), CURRENT_USER()"
        )

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


def test_cognitive_schema():
    print("\n=== EVA MEMORY CORTEX ===")

    try:
        store = MemoryStore()
        store.initialize()

        cortex = MemoryCortex(store)
        cortex.initialize()

        stats = store.stats()

        required_base = [
            "conversations",
            "memories",
            "identity_profile",
            "relationships",
            "emotional_state",
            "goals",
            "internal_events",
            "decisions"
        ]

        for table in required_base:
            print(
                f"{table:20}: "
                f"{stats.get(table, 0)} registros"
            )

        status = cortex.status()
        print(
            f"{'entities':20}: "
            f"{status.get('entities', 0)} registros"
        )
        print(
            f"{'memory_tree':20}: "
            f"{status.get('tree_branches', 0)} ramas"
        )
        print(
            f"{'tasks':20}: "
            f"{status.get('tasks', 0)} pendientes"
        )

        print("OK: esquema cognitivo v0.4.0 preparado.")
        return True

    except Exception as exc:
        print("ERROR MEMORY CORTEX:", exc)
        return False


if __name__ == "__main__":
    ollama_ok, embedding_ok = test_ollama()
    mysql_ok = test_mysql()

    cognitive_ok = False

    if mysql_ok:
        cognitive_ok = test_cognitive_schema()

    print("\n=== RESULTADO ===")
    print(
        "Ollama chat   :",
        "OK" if ollama_ok else "FALLO"
    )
    print(
        "Embeddings    :",
        (
            "OK"
            if embedding_ok
            else "FALLBACK LEXICAL"
        )
    )
    print(
        "MySQL         :",
        "OK" if mysql_ok else "FALLO"
    )
    print(
        "Memory Cortex :",
        "OK" if cognitive_ok else "FALLO"
    )

    if not (ollama_ok and mysql_ok and cognitive_ok):
        sys.exit(1)

    print("\nTodo listo para iniciar EVA v0.4.0.")
