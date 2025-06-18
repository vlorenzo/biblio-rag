"""Minimal token counting helpers.

Try to use *tiktoken* if available; otherwise fall back to a naive word-count × 0.75
heuristic which is obviously inaccurate but good enough for guardrails in unit
tests.
"""

from __future__ import annotations

from typing import List, Dict, Any
import json

try:
    import tiktoken  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    tiktoken = None  # type: ignore


_DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"


def count_tokens(messages: List[Dict[str, Any]], model: str | None = None) -> int:
    """Return estimated token count for a list-of-dict chat messages."""
    if tiktoken is None:
        # naïve fallback: 1 token ≈ 4 chars
        total_chars = 0
        for m in messages:
            content = m.get("content", "")
            if content:
                total_chars += len(content)
            # Also count tool calls if present
            if "tool_calls" in m and m["tool_calls"]:
                total_chars += len(json.dumps(m["tool_calls"]))
        return int(total_chars / 4)

    enc = tiktoken.encoding_for_model(model or _DEFAULT_CHAT_MODEL)
    total_tokens = 0
    
    for m in messages:
        # Handle content field (can be None for assistant messages with tool calls)
        content = m.get("content", "")
        if content:
            total_tokens += len(enc.encode(content))
        
        # Also count tool calls if present
        if "tool_calls" in m and m["tool_calls"]:
            # Convert tool calls to string and count tokens
            tool_calls_str = json.dumps(m["tool_calls"])
            total_tokens += len(enc.encode(tool_calls_str))
    
    return total_tokens 