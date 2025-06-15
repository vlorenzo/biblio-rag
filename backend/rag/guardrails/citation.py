"""Citation helpers."""

from __future__ import annotations

import re
from typing import Dict

from backend.rag.guardrails.errors import CitationError

# regex to capture citation indexes like [1], [23]
_CITATION_RE = re.compile(r"\[(\d+)\]")


def extract_used_citation_indexes(answer_text: str) -> set[int]:
    """Return the set of citation indexes referenced in the answer text."""
    return {int(match) for match in _CITATION_RE.findall(answer_text)}


def validate_citations(answer_text: str, citation_map: Dict[int, dict]) -> None:
    """Ensure that every citation in the answer exists in citation_map."""
    used = extract_used_citation_indexes(answer_text)
    missing = {idx for idx in used if idx not in citation_map}
    if missing:
        raise CitationError(f"Missing citations for indexes: {sorted(missing)}") 