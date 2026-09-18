from flask import Flask, render_template, request, jsonify
from brain.agent import EvaAgent
from config import APP_NAME, APP_VERSION, HOST, PORT, DEBUG

app = Flask(__name__)
eva = EvaAgent()

@app.get("/")
def index():
    return render_template("index.html", app_name=APP_NAME, version=APP_VERSION)

@app.get("/api/state")
def state():
    return jsonify(eva.get_state())

@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Mensaje vacio"}), 400
    return jsonify(eva.respond(message))

if __name__ == "__main__":
    eva.initialize()
    app.run(host=HOST, port=PORT, debug=DEBUG)
