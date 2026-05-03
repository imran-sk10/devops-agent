"""
Local webhook server for the DevOps AI Agent.

Endpoints:
  GET  /health   — check server + model status
  POST /ask      — submit a question, get an answer

Every POST /ask request must include:
  Header:  X-Agent-Secret: <value from .env>
  Body:    {"question": "your question here"}

Run:
  python agent/server.py
"""

import os
import sys

# Make sure agent.py in the same folder is importable
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from agent import run, OLLAMA_HOST, OLLAMA_MODEL

load_dotenv()

AGENT_SECRET = os.getenv("AGENT_SECRET", "devops123")
AGENT_PORT   = int(os.getenv("AGENT_PORT", 5050))

app = Flask(__name__)


def authorized() -> bool:
    """Check the X-Agent-Secret header matches our secret."""
    return request.headers.get("X-Agent-Secret", "") == AGENT_SECRET


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":      "ok",
        "ollama_host": OLLAMA_HOST,
        "model":       OLLAMA_MODEL,
    })


@app.route("/ask", methods=["POST"])
def ask():
    # Auth
    if not authorized():
        return jsonify({"error": "Unauthorized — wrong or missing X-Agent-Secret header"}), 401

    # Parse body
    body = request.get_json(silent=True)
    if not body or "question" not in body:
        return jsonify({"error": "Body must be JSON with a 'question' field"}), 400

    question = body["question"].strip()
    if not question:
        return jsonify({"error": "'question' cannot be empty"}), 400

    print(f"\n[server] Question: {question}")

    try:
        output = run(question)
    except SystemExit as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

    return jsonify({
        "question": question,
        "answer":   output,
    })


if __name__ == "__main__":
    print(f"[server] DevOps Agent starting...")
    print(f"[server] Ollama : {OLLAMA_HOST}  (model: {OLLAMA_MODEL})")
    print(f"[server] Port   : {AGENT_PORT}")
    print(f"[server] Health : http://localhost:{AGENT_PORT}/health")
    print(f"[server] Ask    : POST http://localhost:{AGENT_PORT}/ask")
    app.run(host="0.0.0.0", port=AGENT_PORT, debug=False)
