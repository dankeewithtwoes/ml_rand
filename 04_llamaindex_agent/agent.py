#!/usr/bin/env python3
"""Stateful LlamaIndex ReAct agent with router and graceful fallback."""

import argparse
import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, Field
from safe_math import evaluate
from web_search import WebSearchError, search_web


load_dotenv()


class AgentResponse(BaseModel):
    answer: str = Field(description="Final answer to the user's question")
    reasoning: str = Field(description="Short reasoning summary")
    tools_used: List[str] = Field(description="Names of tools used")
    confidence: str = Field(description="high | medium | low")


def inventory_tool() -> str:
    """Return current inventory counts and prices."""
    return json.dumps({
        "Widget Pro": {"price": 120, "stock": 45},
        "Widget Lite": {"price": 45, "stock": 120},
    })


def calculator_tool(expression: str) -> str:
    """Evaluate a simple math expression safely."""
    try:
        return str(evaluate(expression))
    except Exception as e:
        return f"Error: {e}"


def web_search_fallback(query: str) -> str:
    """Search the live web through a keyless provider and include provenance."""
    try:
        return json.dumps(search_web(query), ensure_ascii=False)
    except WebSearchError as exc:
        return f"WEB_SEARCH_ERROR: {exc}"


def build_agent(docs_dir: Path):
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    if api_key:
        Settings.llm = OpenAI(model=model, api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL"))
    else:
        print("OPENAI_API_KEY not set; using local Ollama (llama3.1)")
        Settings.llm = OpenAI(
            model="llama3.1",
            api_key="ollama",
            api_base="http://localhost:11434/v1",
            temperature=0.2,
        )

    documents = SimpleDirectoryReader(str(docs_dir)).load_data()
    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine()

    tools = [
        QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="company_docs",
                description="Answers questions about company products, pricing, and target audience.",
            ),
        ),
        FunctionTool.from_defaults(fn=inventory_tool),
        FunctionTool.from_defaults(fn=calculator_tool),
        FunctionTool.from_defaults(fn=web_search_fallback),
    ]

    memory = ChatMemoryBuffer.from_defaults(token_limit=2048)
    agent = ReActAgent.from_tools(tools, memory=memory, verbose=True)
    return agent


def main(question: str, docs_dir: Path, interactive: bool):
    agent = build_agent(docs_dir)

    if interactive:
        print("Interactive mode. Type 'exit' to quit.")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
    else:
        response = agent.chat(question)
        print("\n--- Final response ---")
        print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question", default="What is the total value of inventory?", nargs="?")
    parser.add_argument("--docs-dir", type=Path, default="documents")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    main(args.question, args.docs_dir, args.interactive)
