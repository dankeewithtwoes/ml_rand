"""Offline portability checks for tool schemas across OpenAI-compatible providers."""
import re


PROVIDER_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def contract_report(skill, providers: list[str]) -> dict:
    errors = []
    if not PROVIDER_NAME.fullmatch(skill.name): errors.append("tool name is not provider portable")
    if skill.schema.get("type") != "object": errors.append("tool input schema must be an object")
    unsupported = set(skill.schema) - {"$schema", "type", "properties", "required", "additionalProperties", "description"}
    if unsupported: errors.append(f"potentially unsupported schema keywords: {sorted(unsupported)}")
    return {"skill": skill.name, "providers": {provider: not errors for provider in providers}, "errors": errors,
            "portable": not errors}
