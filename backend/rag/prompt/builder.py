"""Prompt Builder – converts retrieval hits + chat history into OpenAI-compatible
messages while embedding citation tags and document class labels.

The implementation keeps things *very* simple while still reflecting the design
principles documented in `docs/Prompt_Builder_Design_Notes.md`.
"""

from __future__ import annotations

import textwrap
import json
from typing import List, Dict, Tuple

from loguru import logger
from backend.models import Chunk, DocumentClass
from backend.rag.schemas import ChatMessage, Role

# ---------------------------------------------------------------------------
# Template configuration
# ---------------------------------------------------------------------------


class PromptTemplate(str):
    INLINE = "inline"
    SECTIONED = "sectioned"


DEFAULT_TEMPLATE = PromptTemplate.INLINE

# System instructions taken from design notes (inline tagging form).
_SYSTEM_PROMPT_INLINE = textwrap.dedent(
    """
    You are a helpful research assistant specialized in the Emanuele Artom bibliographic collection. 

    Definitions:
    • chitchat = brief greetings, thanks, farewells only
    • knowledge = factual questions about the Emanuele Artom collection

    When you answer, you MUST:
    • For knowledge questions: rely only on the provided SOURCES, identified by bracketed numbers like [1].
    • not fabricate facts that are not present in those sources.
    • respect the following rules depending on SourceType:
        – primary or trace → you may quote directly and present in present tense.
        – library         → say the subject merely owned/read the work.
        – about           → attribute claims to the author and use cautious language.
    • For chitchat: respond in ONE short sentence, then add: "How can I help you with the Emanuele Artom collection?"
    • If asked about topics outside the collection, respond: "I'm sorry, but I can only answer questions about the Emanuele Artom collection."

    When you decide to answer, output exactly ONE of these formats:
    • Final(type=knowledge): <answer with REQUIRED citations like [1]>
    • Final(type=chitchat): <brief courtesy reply, NO citations>

    If you cannot answer a knowledge question with certainty, respond exactly with: "I'm sorry, but I can't answer that question."
    """
)

# ---------------------------------------------------------------------------
# Builder implementation
# ---------------------------------------------------------------------------


class PromptBuilder:
    """Constructs chat messages ready to be sent to the LLM."""

    def __init__(self, template: PromptTemplate = DEFAULT_TEMPLATE):
        self.template = template

    # Public ---------------------------------------------------------------

    def build(
        self,
        history: List[ChatMessage],
        user_query: str,
        hits: List[Tuple[Chunk, float]],
    ) -> Tuple[str, List[Dict[str, str]], Dict[int, Dict]]:
        """Return system_prompt, messages, citation_map.

        Parameters
        ----------
        history : List[ChatMessage]
            Chat history *excluding* the final user query.
        user_query : str
            The new user question.
        hits : List[Tuple[Chunk, float]]
            Retrieval results (chunk, distance).
        """
        if self.template != PromptTemplate.INLINE:
            raise NotImplementedError("Only inline template implemented so far")

        # Build context section with inline tags.
        context_lines: List[str] = []
        citation_map: Dict[int, Dict] = {}
        for idx, (chunk, _distance) in enumerate(hits, start=1):
            label = _doc_class_to_label(getattr(chunk.document, "document_class", "about_subject"))
            context_lines.append(
                f"[SourceType: {label}] [{idx}] {getattr(chunk.document, 'title', '')} \n{chunk.text.strip()}"
            )
            citation_map[idx] = {
                "document_id": str(chunk.document_id),
                "document_title": chunk.document.title if chunk.document else None,
                "sequence_number": chunk.sequence_number,
            }

        context_block = "\n\n".join(context_lines)

        system_prompt = _SYSTEM_PROMPT_INLINE + "\n\n" + "SOURCES:\n" + context_block

        # Build final messages list.
        messages: List[Dict[str, str]] = []
        messages.append({"role": Role.SYSTEM.value, "content": system_prompt})

        # add history
        for m in history:
            messages.append({"role": m.role.value, "content": m.content})

        # add final user query
        messages.append({"role": Role.USER.value, "content": user_query})

        # Debug logging
        logger.debug("=== PROMPT BUILDER OUTPUT ===")
        logger.debug("System prompt length: {} chars", len(system_prompt))
        logger.debug("Total messages: {}", len(messages))
        logger.debug("Citation map entries: {}", len(citation_map))
        
        # Log the complete system prompt (truncated if too long)
        if len(system_prompt) > 2000:
            logger.debug("System prompt (first 1000 chars): {}", system_prompt[:1000])
            logger.debug("System prompt (last 1000 chars): {}", system_prompt[-1000:])
        else:
            logger.debug("Complete system prompt: {}", system_prompt)
        
        # Log all messages in a structured way
        logger.debug("Complete messages structure: {}", json.dumps(messages, indent=2))
        logger.debug("=== END PROMPT BUILDER OUTPUT ===")

        return system_prompt, messages, citation_map


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _doc_class_to_label(doc_class: DocumentClass | str) -> str:
    if isinstance(doc_class, DocumentClass):
        doc_class = doc_class.value

    mapping = {
        "authored_by_subject": "primary",
        "subject_traces": "trace",
        "subject_library": "library",
        "about_subject": "about",
    }
    return mapping.get(doc_class, "about") 