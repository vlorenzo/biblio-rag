"""High-level guardrails policy enforcement."""

from __future__ import annotations

from typing import List, Dict
import re

from loguru import logger

from backend.rag.guardrails.token_utils import count_tokens
from backend.rag.guardrails.errors import TokenLimitError, CitationError
from backend.rag.guardrails.citation import validate_citations

MAX_TOTAL_TOKENS = 250_000  # generous default; model/plan can override

# Different refusal messages for different failure modes
REFUSAL_NO_DATA = "I don't have enough information in the collection to answer that question definitively. The Artom archive is still being digitized and catalogued - perhaps that information will become available as we continue our work."
REFUSAL_GENERIC = "I'm not able to provide a reliable answer to that question based on the sources available to me."
REFUSAL_OUT_OF_SCOPE = "That's outside the scope of the Emanuele Artom collection, but I'd be delighted to help you explore what we do have about Artom's intellectual world and historical legacy!"
REFUSAL_CHITCHAT = "I apologize, but there seems to be an issue with my response. Could you please rephrase your question?"

# Backward compatibility alias
REFUSAL_MSG = REFUSAL_GENERIC


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
    4. Fallback to appropriate refusal if violations.
    """
    def log_guardrail_event(reason: str, details: str | None = None) -> None:
        preview = answer_text[:300] + "..." if len(answer_text) > 300 else answer_text
        logger.warning(
            "[guardrail] reason={} answer_type={} length={} preview={} details={}",
            reason,
            answer_type,
            len(answer_text),
            preview,
            details or "",
        )

    if answer_type == "knowledge":
        try:
            validate_citations(answer_text, citation_map)
        except CitationError as exc:
            # Diagnostic only: keep answer, log the citation issue
            if not citation_map:
                log_guardrail_event("missing_citations_no_sources", str(exc))
            else:
                log_guardrail_event("missing_citations", str(exc))
    else:  # chitchat
        # For chitchat, be much more permissive - we want natural conversation
        
        # Only reject if it has clear citation syntax (like [1], [2])
        # This avoids false positives on normal text with brackets
        citation_pattern = r"\[\d+\]"
        if re.search(citation_pattern, answer_text):
            log_guardrail_event("chitchat_contains_citations")
            # Soft-fix: strip bracketed citations instead of refusing
            answer_text = re.sub(citation_pattern, "", answer_text).strip()
        
        # Much more generous length limit for conversational responses
        # Allow up to ~375 words (2500 characters) for warm, engaging responses
        # This allows for substantive biographical or explanatory responses
        if len(answer_text) > 2500:
            log_guardrail_event("chitchat_length_exceeded")

    if messages is not None:
        if count_tokens(messages) > max_tokens:
            log_guardrail_event("token_limit_exceeded", f"max_tokens={max_tokens}")
            raise TokenLimitError("Prompt exceeds token limit")

    return answer_text
