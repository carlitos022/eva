from flask import Flask, render_template, request, jsonify

from brain.agent import EvaAgent
from config import APP_NAME, APP_VERSION, HOST, PORT, DEBUG


app = Flask(__name__)
eva = EvaAgent()


@app.get("/")
def index():
    return render_template(
        "index.html",
        app_name=APP_NAME,
        version=APP_VERSION
    )


@app.get("/api/state")
def state():
    return jsonify(eva.get_state())


@app.get("/api/cognition")
def cognition():
    state = eva.get_state()

    return jsonify({
        "identity": state.get("identity", []),
        "relationship": state.get("relationship", {}),
        "goals": state.get("goals", []),
        "emotion": {
            "emotion": state.get("emotion"),
            "intensity": state.get("intensity"),
            "trust": state.get("trust"),
            "energy": state.get("energy"),
            "curiosity": state.get("curiosity")
        },
        "stats": state.get("stats", {})
    })


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Mensaje vacio"}), 400

    try:
        return jsonify(eva.respond(message))
    except Exception as exc:
        app.logger.exception(
            "Error procesando mensaje de EVA"
        )

        return jsonify({
            "error": "EVA no pudo procesar el mensaje.",
            "detail": str(exc) if DEBUG else ""
        }), 500


if __name__ == "__main__":
    eva.initialize()
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )
