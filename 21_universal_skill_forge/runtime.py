#!/usr/bin/env python3
"""Runtime adapters for local and cloud LLM providers."""
import os
from typing import Any


def parse_model_ref(ref: str) -> tuple:
    """Parse 'provider/model' e.g. ollama/llama3.1 or openai/gpt-4o-mini."""
    if "/" in ref:
        provider, model = ref.split("/", 1)
        return provider, model
    return "ollama", ref


def call_model(model_ref: str, messages: list, tools: list) -> Any:
    provider, model = parse_model_ref(model_ref)
    try:
        from openai import OpenAI
    except Exception as exc:
        return {"error": f"openai SDK unavailable: {exc}"}

    if provider == "ollama":
        client = OpenAI(api_key="ollama", base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"))
    elif provider == "openai":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"), base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    else:
        return {"error": f"unknown provider {provider}"}

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            temperature=0.2,
        )
        return resp
    except Exception as exc:
        return {"error": str(exc)}


def format_tools_for_provider(provider: str, skills: list) -> list:
    tools = []
    for skill in skills:
        tool = {
            "type": "function",
            "function": {
                "name": skill.name,
                "description": skill.description,
                "parameters": skill.schema,
            },
        }
        tools.append(tool)
    return tools
