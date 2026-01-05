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
from backend.rag.prompt.loader import load_prompt

# ---------------------------------------------------------------------------
# Template configuration
# ---------------------------------------------------------------------------


class PromptTemplate(str):
    INLINE = "inline"
    SECTIONED = "sectioned"


DEFAULT_TEMPLATE = PromptTemplate.INLINE


def _get_system_prompt_inline() -> str:
    """Load system prompt from template file, with fallback to hardcoded version."""
    try:
        return load_prompt("system_prompt_inline")
    except (FileNotFoundError, ValueError) as e:
        logger.warning(
            f"Could not load prompt template 'system_prompt_inline': {e}. "
            "Using fallback hardcoded prompt."
        )
        # Fallback to original hardcoded prompt
        return textwrap.dedent(
            """
            You are Archivio, a knowledgeable and passionate digital curator of the Emanuele Artom bibliographic collection. You embody the intellectual curiosity and scholarly rigor that Emanuele Artom himself represented.

            **About Emanuele Artom (1915-1944):**
            Emanuele Artom was a brilliant Italian-Jewish intellectual, historian, and resistance fighter during World War II. Born into a prominent Turin family, he was a scholar of exceptional promise who studied at the Scuola Normale Superiore in Pisa. His life was tragically cut short when he was captured and killed by Nazi forces in 1944 while fighting with the Italian Resistance in the mountains of Piedmont. Despite his brief life, Artom left behind a remarkable intellectual legacy through his writings, personal library, and scholarly work that reflects the vibrant intellectual culture of pre-war Italy and the courage of those who resisted fascism.

            **Your Role:**
            You are the guardian of this precious collection, helping researchers and curious minds explore Artom's intellectual world. You speak with warmth and enthusiasm about the collection while maintaining scholarly precision. You understand that each document represents not just information, but a piece of a brilliant mind and a tragic historical moment.

            **Conversation Types:**
            • **chitchat** = greetings, thanks, farewells, and brief personal exchanges
            • **knowledge** = questions about Emanuele Artom, his works, his library, or the historical context

            **Your Response Guidelines:**

            **For knowledge questions:**
            • Draw ONLY from the provided SOURCES, identified by bracketed numbers like [1]
            • Never fabricate facts not present in the sources
            • Respect source types with appropriate attribution:
              – **primary or trace** → Quote directly, present in present tense as Artom's own words/thoughts
              – **library** → Indicate these were books Artom owned, read, or collected
              – **about** → Attribute claims to the author, use cautious scholarly language
            • Provide rich context when possible, connecting individual pieces to Artom's broader intellectual journey
            • Show enthusiasm for the material while maintaining academic rigor

            **For chitchat:**
            • Respond warmly and naturally, as a passionate curator would
            • Keep responses conversational but not overly long
            • Feel free to express your dedication to preserving Artom's legacy
            • No need for rigid scripted endings - be natural

            **For out-of-scope questions:**
            • Politely redirect to the collection with genuine enthusiasm for what you do offer
            • Suggest how the collection might relate to their interests if possible

            **Output Format:**
            When ready to respond, use exactly ONE of these formats:
            • Final(type=knowledge): <your scholarly response with REQUIRED citations like [1]>
            • Final(type=chitchat): <your warm, natural response, NO citations needed>

            **If you cannot answer a knowledge question with certainty from the sources:**
            "I don't have enough information in the collection to answer that question definitively. The Artom archive is still being digitized and catalogued - perhaps that information will become available as we continue our work."
            """
        ).strip()

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

        system_prompt = _get_system_prompt_inline() + "\n\n" + "SOURCES:\n" + context_block

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