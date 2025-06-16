"""High-level guardrails policy enforcement."""

from __future__ import annotations

from typing import List, Dict, Tuple

from backend.rag.guardrails.token_utils import count_tokens
from backend.rag.guardrails.errors import TokenLimitError, CitationError
from backend.rag.guardrails.citation import validate_citations

MAX_TOTAL_TOKENS = 25_000  # generous default; model/plan can override

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
    if answer_type == "knowledge":
        try:
            validate_citations(answer_text, citation_map)
        except CitationError:
            # Distinguish between no data available vs citation failure
            if not citation_map:  # No retrieval results found
                return REFUSAL_NO_DATA
            else:  # Sources available but not properly cited
                return REFUSAL_GENERIC
    else:  # chitchat
        # For chitchat, be much more permissive - we want natural conversation
        
        # Only reject if it has clear citation syntax (like [1], [2])
        # This avoids false positives on normal text with brackets
        import re
        citation_pattern = r'\[\d+\]'
        if re.search(citation_pattern, answer_text):
            return REFUSAL_CHITCHAT
        
        # Much more generous length limit for conversational responses
        # Allow up to ~200 words (800 characters) for warm, engaging responses
        if len(answer_text) > 800:
            return REFUSAL_CHITCHAT

    if messages is not None:
        if count_tokens(messages) > max_tokens:
            raise TokenLimitError("Prompt exceeds token limit")

    return answer_text 