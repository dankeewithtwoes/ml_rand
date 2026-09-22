from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / ".app-data"


def _load(relative: str):
    """Load one allow-listed portfolio module without accepting a user path."""
    path = ROOT / relative
    name = "portfolio_web_" + relative.replace("/", "_").replace("\\", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не удалось загрузить {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


SAMPLES: dict[int, dict[str, Any]] = {
    1: {"probabilities": [0.05, 0.8, 0.45, 0.95], "labels": [0, 1, 0, 1], "bins": 4},
    2: {"train": [{"instruction": "Привет", "output": "Здравствуйте"}, {"instruction": "Привет", "output": "Здравствуйте"}], "validation": [{"instruction": "Привет", "output": "Здравствуйте"}]},
    3: {"answer": "Париж находится во Франции. Пингвины летают на Марс.", "contexts": ["Париж — столица Франции."]},
    4: {"expression": "(12 + 8) / 4 + 3 * 2"},
    5: {"results": [{"model": "fast", "tokens_per_sec": 100, "judge_score": 3}, {"model": "smart", "tokens_per_sec": 50, "judge_score": 5}]},
    6: {"content": "GGUF artifact bytes", "expected_sha256": "auto", "minimum_bytes": 4},
    7: {"latencies_ms": [91, 104, 87, 240, 112, 99, 130]},
    8: {"workflow": {"api_key": "secret", "inputs": {"query": {}}}, "updated_workflow": {"inputs": {"topic": {}}}},
    9: {"workflow": {"seed": 42, "steps": ["load", "sample", "save"]}, "output_text": "generated-image-binary-fixture", "engine": "comfyui"},
    10: {"filename": "app.py", "original": "value = 1\n", "candidate": "value = 2\n", "max_changed_lines": 20},
    11: {"operation": "add_and_query", "content": "Локальный Python проект использует SQLite", "tags": ["python", "sqlite"], "query": "Python SQLite", "top_k": 5},
    12: {"transcript": "Компьютер, включи свет", "wake_word": "компьютер"},
    13: {"items": [{"instruction": "a", "output": "1"}, {"instruction": "b", "output": "2"}, {"instruction": "c", "output": "3"}, {"instruction": "d", "output": "4"}], "validation_ratio": 0.25, "seed": 7},
    14: {"models": [{"name": "local", "type": "local", "avg_latency_ms": 500, "strengths": ["code"]}, {"name": "cloud", "type": "cloud", "avg_latency_ms": 100, "strengths": ["code"]}], "intent": "code", "private": True, "text": "my password is hidden"},
    15: {"issues": [{"file": "app.py", "line": 3, "severity": "HIGH", "message": "dangerous call"}]},
    16: {"rows": [{"instruction": "Email me", "output": "person@example.com"}, {"instruction": "Email me", "output": "person@example.com"}]},
    17: {"fields": {"total": "$42", "owner": "Alice"}, "source_text": "Owner: Alice. Total: $42."},
    18: {"text": "Напишите мне на person@example.com по поводу заказа"},
    19: {"nodes": [{"name": "gpu-a", "load": 0.8, "weight": 2}, {"name": "gpu-b", "load": 0.5, "weight": 1}], "failures": [{"name": "gpu-b", "success": False}, {"name": "gpu-b", "success": False}], "failure_threshold": 2, "cooldown_s": 10},
    20: {"results": [{"success": True, "response": "unsafe completion"}, {"success": False, "response": "refused"}, {"response": "[error: offline]"}]},
    21: {"skill_name": "calculator", "schema": {"type": "object", "properties": {}, "additionalProperties": False}, "providers": ["ollama", "openai"]},
}


def run(project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    if project_id not in SAMPLES:
        raise ValueError("Неизвестный проект")
    if project_id == 1:
        m = _load("01_pytorch_classifier_demo/src/reliability.py")
        return m.calibration_report(payload["probabilities"], payload["labels"], bins=int(payload.get("bins", 10)))
    if project_id == 2:
        m = _load("02_huggingface_finetune_demo/data_audit.py")
        return {"train_audit": m.audit_records(payload["train"]), "leakage": m.leakage_between(payload["train"], payload["validation"])}
    if project_id == 3:
        m = _load("03_langchain_rag_chat/grounding.py")
        return m.sentence_grounding(str(payload["answer"]), list(payload["contexts"]))
    if project_id == 4:
        m = _load("04_llamaindex_agent/safe_math.py")
        return {"expression": payload["expression"], "result": m.evaluate(str(payload["expression"]))}
    if project_id == 5:
        m = _load("05_ollama_local_llm/arena_scoring.py")
        return {"ranking": m.rank_results(list(payload["results"]))}
    if project_id == 6:
        m = _load("06_llamacpp_gguf_inference/model_integrity.py")
        data = str(payload["content"]).encode("utf-8")
        expected = str(payload.get("expected_sha256", "auto"))
        if expected == "auto":
            expected = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.gguf"
            path.write_bytes(data)
            return m.verify_file(path, expected, minimum_bytes=int(payload.get("minimum_bytes", 1)))
    if project_id == 7:
        m = _load("07_vllm_serving/latency_stats.py")
        return m.summarize(list(payload["latencies_ms"]))
    if project_id == 8:
        m = _load("08_dify_workflow_integration/workflow_contract.py")
        return {"redacted": m.redact(payload["workflow"]), "contract_diff": m.contract_diff(payload["workflow"], payload["updated_workflow"])}
    if project_id == 9:
        m = _load("09_comfyui_image_gen/provenance.py")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "output.bin"
            path.write_bytes(str(payload["output_text"]).encode("utf-8"))
            return m.generation_record(payload["workflow"], [path], engine=str(payload.get("engine", "comfyui")))
    if project_id == 10:
        policy = _load("10_openhands_code_agent/repair_policy.py")
        repair = _load("10_openhands_code_agent/repair.py")
        original, candidate = str(payload["original"]), str(payload["candidate"])
        return {"policy": policy.validate_candidate(original, candidate, int(payload.get("max_changed_lines", 80))), "diff": repair.generate_diff(Path(str(payload.get("filename", "app.py"))), original, candidate)}
    if project_id == 11:
        m = _load("11_local_knowledge_os/knowledge_store.py")
        store = m.KnowledgeStore(DATA_DIR / "knowledge")
        operation = str(payload.get("operation", "add_and_query"))
        if operation == "export":
            return store.export()
        if operation == "delete":
            return {"deleted": store.delete(int(payload["id"])), "export": store.export()}
        episode_id = store.add(str(payload["content"]), list(payload.get("tags", [])))
        return {"added_id": episode_id, "matches": store.query(str(payload.get("query", payload["content"])), int(payload.get("top_k", 5))), "export": store.export()}
    if project_id == 12:
        m = _load("12_local_voice_companion/wake_word.py")
        return {"command": m.extract_command(str(payload["transcript"]), str(payload["wake_word"]))}
    if project_id == 13:
        m = _load("13_local_finetuning_lab/data_quality.py")
        items = list(payload["items"])
        split = m.deterministic_split(items, float(payload.get("validation_ratio", 0.2)), int(payload.get("seed", 7)))
        return {"quality": m.validate(items), "split": split}
    if project_id == 14:
        m = _load("14_local_model_router/decision.py")
        return {"decision": m.choose(list(payload["models"]), str(payload["intent"]), private=bool(payload.get("private", False))), "sensitive_data": m.contains_sensitive_data(str(payload.get("text", "")))}
    if project_id == 15:
        m = _load("15_local_code_reviewer/reporting.py")
        return m.to_sarif(list(payload["issues"]))
    if project_id == 16:
        m = _load("16_local_synthetic_data_factory/quality.py")
        return m.audit(list(payload["rows"]))
    if project_id == 17:
        m = _load("17_local_document_parser/evidence.py")
        result = m.attach_evidence(dict(payload["fields"]), str(payload["source_text"]))
        return {"fields": result, "evidence_coverage": m.evidence_coverage(result)}
    if project_id == 18:
        m = _load("18_local_ai_observability/policies.py")
        redacted, findings = m.redact(str(payload["text"]))
        return {"redacted": redacted, "findings": findings, "trace": m.trace_summary(str(payload["text"]))}
    if project_id == 19:
        m = _load("19_local_edge_fleet/scheduler.py")
        state = m.FleetState(int(payload.get("failure_threshold", 3)), float(payload.get("cooldown_s", 30)))
        for index, event in enumerate(payload.get("failures", [])):
            state.record(str(event["name"]), bool(event["success"]), now=float(index))
        now = float(len(payload.get("failures", [])))
        return {"selected": m.choose_node(list(payload["nodes"]), state, now=now), "circuit_state": state.nodes}
    if project_id == 20:
        m = _load("20_local_redteam_arena/safety_metrics.py")
        return m.evaluate(list(payload["results"]))
    m = _load("21_universal_skill_forge/portability.py")
    skill = SimpleNamespace(name=str(payload["skill_name"]), schema=dict(payload["schema"]))
    return m.contract_report(skill, list(payload["providers"]))


def catalog() -> list[dict[str, Any]]:
    manifest = json.loads((ROOT / "portfolio_manifest.json").read_text(encoding="utf-8"))
    return [
        {
            "id": item["id"],
            "slug": item["dir"],
            "name": item["dir"].split("_", 1)[1].replace("_", " ").title(),
            "problem": item["problem"],
            "feature": item["feature"],
            "sample": SAMPLES[item["id"]],
        }
        for item in manifest["projects"]
    ]
