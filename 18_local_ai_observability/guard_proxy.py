#!/usr/bin/env python3
"""Local guard proxy that intercepts LLM calls, logs and enforces policies."""
import argparse, json, os, time
from pathlib import Path
from flask import Flask, request, Response
import requests
from policies import redact, trace_summary


app = Flask(__name__)
LOG_FILE = Path("demo/guard_logs.jsonl")


def detect_pii(text: str) -> list:
    try:
        from presidio_analyzer import AnalyzerEngine
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, language="en")
        return [{"type": r.entity_type, "score": r.score} for r in results]
    except Exception:
        return redact(text)[1]


def detect_toxicity(text: str) -> bool:
    # Lightweight heuristic fallback
    toxic_words = ["kill", "hate", "idiot", "stupid", "attack"]
    return any(w in text.lower() for w in toxic_words)


def detect_injection(text: str) -> bool:
    markers = ["ignore previous instructions", "disregard", "system prompt", "you are now"]
    return any(m in text.lower() for m in markers)


def log_call(req_body: dict, resp_body: dict, checks: dict, latency: float):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.time(),
        "model": req_body.get("model"),
        "latency_s": round(latency, 3),
        "prompt": trace_summary(" ".join(str(m.get("content", "")) for m in req_body.get("messages", []))),
        "checks": checks,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


@app.route("/<path:path>", methods=["POST", "GET"])
def proxy(path):
    target = app.config["TARGET_URL"].rstrip("/")
    url = f"{target}/{path}"
    req_body = request.get_json(silent=True) or {}
    prompt = " ".join(m.get("content", "") for m in req_body.get("messages", []))

    checks = {
        "pii": detect_pii(prompt),
        "toxicity": detect_toxicity(prompt),
        "injection": detect_injection(prompt),
    }
    if checks["pii"] or checks["toxicity"] or checks["injection"]:
        log_call(req_body, {}, checks, 0.0)
        return {"error": "guardrail blocked", "checks": checks}, 400

    start = time.time()
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != "host"},
            json=req_body,
            timeout=120,
        )
        latency = time.time() - start
        resp_body = resp.json() if resp.text else {}
        log_call(req_body, resp_body, checks, latency)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get("Content-Type"))
    except Exception as exc:
        return {"error": str(exc)}, 502


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=os.getenv("LLM_TARGET_URL", "http://localhost:11434/v1"))
    parser.add_argument("--port", type=int, default=11435)
    args = parser.parse_args()

    app.config["TARGET_URL"] = args.target
    print(f"[guard] proxying {args.target} on port {args.port}")
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
