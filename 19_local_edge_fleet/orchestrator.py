#!/usr/bin/env python3
"""Orchestrator for edge AI fleet."""
import argparse, json, time
from pathlib import Path
from flask import Flask, request, jsonify
import requests
import yaml
from scheduler import FleetState, choose_node


app = Flask(__name__)


def load_nodes(path: Path) -> list:
    if not path.exists():
        return [{"name": "node-1", "url": "http://localhost:9001", "weight": 1}]
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("nodes", [])


def health_check(node: dict) -> bool:
    try:
        resp = requests.get(f"{node['url']}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def select_node(nodes: list, policy: str, state: FleetState | None = None) -> dict:
    state = state or FleetState()
    healthy = [n for n in nodes if state.available(n["name"]) and health_check(n)]
    if not healthy:
        return None
    if policy == "round-robin":
        idx = getattr(select_node, "_idx", 0) % len(healthy)
        select_node._idx = idx + 1
        return healthy[idx]
    return choose_node(healthy, state)


@app.route("/v1/chat/completions", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    nodes = app.config["NODES"]
    policy = app.config["POLICY"]
    state = app.config["FLEET_STATE"]
    node = select_node(nodes, policy, state)
    if node is None:
        return jsonify({"error": "no healthy nodes"}), 503
    try:
        resp = requests.post(f"{node['url']}/v1/chat/completions", json=data, timeout=120)
        state.record(node["name"], resp.status_code < 500)
        return jsonify(resp.json()), resp.status_code
    except Exception as exc:
        state.record(node["name"], False)
        return jsonify({"error": str(exc), "node": node["name"]}), 502


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", default="nodes.yaml")
    parser.add_argument("--port", type=int, default=9090)
    parser.add_argument("--policy", default="round-robin", choices=["round-robin", "least-load"])
    args = parser.parse_args()

    app.config["NODES"] = load_nodes(Path(args.nodes))
    app.config["POLICY"] = args.policy
    app.config["FLEET_STATE"] = FleetState()
    print(f"[orchestrator] {len(app.config['NODES'])} nodes, policy={args.policy}, port={args.port}")
    app.run(host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
