"""Stateful edge scheduler with cooldown-based circuit breaking."""
import time


class FleetState:
    def __init__(self, failure_threshold: int = 3, cooldown_s: float = 30):
        self.failure_threshold, self.cooldown_s, self.nodes = failure_threshold, cooldown_s, {}

    def record(self, name: str, success: bool, now: float | None = None):
        now = time.time() if now is None else now
        state = self.nodes.setdefault(name, {"failures": 0, "open_until": 0.0})
        if success: state.update(failures=0, open_until=0.0)
        else:
            state["failures"] += 1
            if state["failures"] >= self.failure_threshold: state["open_until"] = now + self.cooldown_s

    def available(self, name: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return self.nodes.get(name, {}).get("open_until", 0) <= now


def choose_node(nodes: list[dict], state: FleetState, now: float | None = None) -> dict | None:
    candidates = [node for node in nodes if state.available(node["name"], now)]
    if not candidates: return None
    return min(candidates, key=lambda node: (node.get("load", 0) / max(node.get("weight", 1), .001), node["name"]))
