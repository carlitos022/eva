from waitress import serve

from app import app, eva
from config import HOST, PORT


if __name__ == "__main__":
    eva.initialize()
    print(f"EVA escuchando en http://{HOST}:{PORT}")
    serve(
        app,
        host=HOST,
        port=PORT,
        threads=4,
        channel_timeout=120,
    )
