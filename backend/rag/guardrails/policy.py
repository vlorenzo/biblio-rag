"""High-level guardrails policy enforcement."""

from __future__ import annotations

from typing import List, Dict, Tuple

from backend.rag.guardrails.token_utils import count_tokens
from backend.rag.guardrails.errors import TokenLimitError, CitationError
from backend.rag.guardrails.citation import validate_citations

MAX_TOTAL_TOKENS = 6_000  # generous default; model/plan can override

REFUSAL_MSG = "I'm sorry, but I can't answer that question."


def apply_guardrails(
    answer_text: str,
    citation_map: Dict[int, dict],
    messages: List[Dict[str, str]] | None = None,
    max_tokens: int = MAX_TOTAL_TOKENS,
    answer_type: str = "knowledge",
) -> str:
    """Return the final answer after applying guardrails.

    1. Check citation validity (for knowledge answers).
    2. Check chitchat constraints (for chitchat answers).
    3. Check token budget (if `messages` provided).
    4. Fallback to `REFUSAL_MSG` if violations.
    """
    if answer_type == "knowledge":
        try:
            validate_citations(answer_text, citation_map)
        except CitationError:
            return REFUSAL_MSG
    else:  # chitchat
        # Reject if it accidentally included citation-like patterns
        if "[" in answer_text and "]" in answer_text:
            return REFUSAL_MSG
        # Simple length check (approximate 30 tokens = ~120 characters)
        if len(answer_text) > 120:
            return REFUSAL_MSG

    if messages is not None:
        if count_tokens(messages) > max_tokens:
            raise TokenLimitError("Prompt exceeds token limit")

    return answer_text 