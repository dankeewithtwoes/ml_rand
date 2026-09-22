"""Keyless web search used by the agent's external-search tool.

DuckDuckGo's Instant Answer endpoint is queried directly.  The endpoint does
not require an API key; when it has no useful answer (or the network is
unavailable), callers receive an explicit exception instead of fabricated
search results.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SEARCH_ENDPOINT = "https://api.duckduckgo.com/"
USER_AGENT = "LlamaIndexRouterAgent/1.0 (+local portfolio project)"
MAX_RESPONSE_BYTES = 2_000_000


class WebSearchError(RuntimeError):
    """Raised when keyless search cannot return a trustworthy result."""


def _download_json(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise WebSearchError(f"DuckDuckGo request failed: {exc}") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise WebSearchError("DuckDuckGo response exceeded the 2 MB safety limit")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WebSearchError("DuckDuckGo returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise WebSearchError("DuckDuckGo returned an unexpected response shape")
    return payload


def _topic_results(topics: list[Any]):
    for topic in topics:
        if not isinstance(topic, dict):
            continue
        nested = topic.get("Topics")
        if isinstance(nested, list):
            yield from _topic_results(nested)
            continue
        text = topic.get("Text")
        url = topic.get("FirstURL")
        if isinstance(text, str) and text.strip() and isinstance(url, str) and url.startswith("http"):
            yield {"title": text.split(" - ", 1)[0], "snippet": text.strip(), "url": url}


def search_web(query: str, *, max_results: int = 5, timeout: float = 10.0) -> dict[str, Any]:
    """Return live keyless search results with provider provenance.

    This is an instant-answer search rather than a full crawl.  An empty
    result is an error so the agent cannot mistake "nothing found" for data.
    """
    query = query.strip()
    if not query:
        raise WebSearchError("search query cannot be empty")
    if not 1 <= max_results <= 10:
        raise WebSearchError("max_results must be between 1 and 10")
    if timeout <= 0:
        raise WebSearchError("timeout must be positive")

    params = urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
    request_url = f"{SEARCH_ENDPOINT}?{params}"
    payload = _download_json(request_url, timeout)

    candidates: list[dict[str, str]] = []
    abstract = payload.get("AbstractText")
    abstract_url = payload.get("AbstractURL")
    if isinstance(abstract, str) and abstract.strip() and isinstance(abstract_url, str) and abstract_url:
        candidates.append({
            "title": str(payload.get("Heading") or query),
            "snippet": abstract.strip(),
            "url": abstract_url,
        })
    for result in payload.get("Results", []):
        if not isinstance(result, dict):
            continue
        text = result.get("Text")
        url = result.get("FirstURL")
        if isinstance(text, str) and text.strip() and isinstance(url, str) and url.startswith("http"):
            candidates.append({"title": text.split(" - ", 1)[0], "snippet": text.strip(), "url": url})
    topics = payload.get("RelatedTopics")
    if isinstance(topics, list):
        candidates.extend(_topic_results(topics))

    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for candidate in candidates:
        if candidate["url"] in seen_urls:
            continue
        seen_urls.add(candidate["url"])
        results.append(candidate)
        if len(results) == max_results:
            break
    if not results:
        raise WebSearchError(
            "DuckDuckGo returned no instant-answer results; try a more specific query"
        )

    return {
        "query": query,
        "results": results,
        "provenance": {
            "provider": "DuckDuckGo Instant Answer",
            "request_url": request_url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
