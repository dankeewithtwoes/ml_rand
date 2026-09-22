#!/usr/bin/env python3
"""Edge inference node."""
import argparse, os, time
from flask import Flask, request, jsonify
import requests


app = Flask(__name__)


def call_local_llm(messages, model_url: str):
    try:
        resp = requests.post(
            f"{model_url}/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'ollama')}"},
            json={"model": "llama3.1", "messages": messages, "temperature": 0.2},
            timeout=120,
        )
        return resp.json(), resp.status_code
    except Exception as exc:
        return {"error": str(exc)}, 502


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "name": app.config["NODE_NAME"], "load": 0.0})


@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    start = time.time()
    result, status = call_local_llm(data.get("messages", []), app.config["MODEL_URL"])
    result["node_latency_s"] = round(time.time() - start, 3)
    return jsonify(result), status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="node-1")
    parser.add_argument("--port", type=int, default=9001)
    parser.add_argument("--model-url", default=os.getenv("LLM_MODEL_URL", "http://localhost:11434/v1"))
    args = parser.parse_args()

    app.config["NODE_NAME"] = args.name
    app.config["MODEL_URL"] = args.model_url
    print(f"[node] {args.name} on port {args.port} -> {args.model_url}")
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
