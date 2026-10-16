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


def health_check(node: dict) -> dict | None:
    try:
        resp = requests.get(f"{node['url']}/health", timeout=2)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def select_node(nodes: list, policy: str, state: FleetState | None = None) -> dict:
    state = state or FleetState()
    healthy = []
    for node in nodes:
        if not state.available(node["name"]):
            continue
        health = health_check(node)
        if health is not None:
            try:
                healthy.append({**node, "load": float(health.get("load", node.get("load", 0)))})
            except (TypeError, ValueError):
                continue
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
    if not isinstance(data, dict) or not isinstance(data.get("messages"), list):
        return jsonify({"error": "messages must be a list"}), 400
    nodes = app.config["NODES"]
    policy = app.config["POLICY"]
    state = app.config["FLEET_STATE"]
    remaining = list(nodes)
    failures = []
    while remaining:
        node = select_node(remaining, policy, state)
        if node is None:
            break
        remaining = [item for item in remaining if item["name"] != node["name"]]
        try:
            resp = requests.post(f"{node['url'].rstrip('/')}/v1/chat/completions", json=data, timeout=120)
            body = resp.json()
            if resp.status_code >= 500:
                state.record(node["name"], False)
                failures.append(node["name"])
                continue
            state.record(node["name"], True)
            return jsonify(body), resp.status_code
        except (requests.RequestException, ValueError):
            state.record(node["name"], False)
            failures.append(node["name"])
    return jsonify({"error": "all reachable nodes failed" if failures else "no healthy nodes",
                    "failed_nodes": failures}), 502 if failures else 503


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
