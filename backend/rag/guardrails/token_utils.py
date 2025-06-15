"""Minimal token counting helpers.

Try to use *tiktoken* if available; otherwise fall back to a naive word-count × 0.75
heuristic which is obviously inaccurate but good enough for guardrails in unit
tests.
"""

from __future__ import annotations

from typing import List, Dict

try:
    import tiktoken  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    tiktoken = None  # type: ignore


_DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"


def count_tokens(messages: List[Dict[str, str]], model: str | None = None) -> int:
    """Return estimated token count for a list-of-dict chat messages."""
    if tiktoken is None:
        # naïve fallback: 1 token ≈ 4 chars
        total_chars = sum(len(m["content"]) for m in messages)
        return int(total_chars / 4)

    enc = tiktoken.encoding_for_model(model or _DEFAULT_CHAT_MODEL)
    return sum(len(enc.encode(m["content"])) for m in messages) 