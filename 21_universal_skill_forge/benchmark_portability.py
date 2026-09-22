#!/usr/bin/env python3
"""Benchmark skill portability across multiple local/cloud models."""
import argparse, json
from pathlib import Path
from skill import Skill, discover_skills
from runtime import call_model, format_tools_for_provider
from portability import contract_report
from skillforge import load_examples


def test_skill_on_model(skill_dir: Path, model_ref: str) -> bool:
    skill = Skill(skill_dir)
    try:
        sample = load_examples(skill)[0]["input"]
        skill.run(sample)
    except Exception:
        return False

    tools = format_tools_for_provider("openai", [skill])
    resp = call_model(model_ref, [{"role": "user", "content": f"Call {skill.name}"}], tools)
    return not (isinstance(resp, dict) and "error" in resp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-dir", default="skills")
    parser.add_argument("--models", default="ollama/llama3.1")
    parser.add_argument("--output", default="demo/portability_benchmark.json")
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]
    skills_dir = Path(args.skills_dir)
    results = []
    total = successes = 0
    for skill in discover_skills(skills_dir):
        skill_dir = skill.path
        skill_results = {"skill": skill.name, "contract": contract_report(skill, sorted({m.split('/', 1)[0] for m in models})), "models": {}}
        for model in models:
            ok = test_skill_on_model(skill_dir, model)
            skill_results["models"][model] = ok
            total += 1
            successes += int(ok)
        results.append(skill_results)

    score = successes / total if total else 0.0
    report = {"portability_score": round(score, 2), "total": total, "successes": successes, "details": results}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[benchmark] portability_score={score:.2f} -> {args.output}")


if __name__ == "__main__":
    main()
