#!/usr/bin/env python3
"""Edge inference node."""
import argparse, os, time
from flask import Flask, request, jsonify
import requests


app = Flask(__name__)


def call_local_llm(payload: dict, model_url: str):
    body = dict(payload)
    body.setdefault("model", "llama3.1")
    body.setdefault("temperature", 0.2)
    base = model_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'ollama')}"},
            json=body,
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
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        return jsonify({"error": "messages must be a list"}), 400
    if data.get("stream"):
        return jsonify({"error": "streaming is not supported by this node"}), 501
    start = time.time()
    result, status = call_local_llm(data, app.config["MODEL_URL"])
    if not isinstance(result, dict):
        return jsonify({"error": "model returned a non-object response"}), 502
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
