"""Lightweight ReAct agent wrapper.

The implementation purposefully avoids full-blown JSON function calling to keep
things framework-agnostic and test-friendly. It relies on a very simple text
protocol:

    Thought: …
    Action: Search["query"]

or

    Thought: …
    Action: Answer
    Final: <answer with citations>

All OpenAI calls are kept behind an overridable `_llm_call()` method so that
unit-tests can monkey-patch it without touching global state.
"""

from __future__ import annotations

import re
import json
from typing import Dict, List, Tuple, Optional

from loguru import logger

from backend.config import settings
from backend.rag.agent import config as cfg
from backend.rag.guardrails import apply_guardrails, REFUSAL_MSG

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_ACTION_RE = re.compile(r"Action:\s*(Search|Answer)(?:\[(.*?)\])?", re.I)
_FINAL_RE = re.compile(r"Final\(type\s*=\s*(\w+)\):\s*(.*)", re.I | re.S)


class ReActAgent:
    """Run a mini ReAct loop and return the final answer + citation indexes."""

    def __init__(self, temperature: float = cfg.TEMPERATURE):
        self.temperature = temperature

        # lazily constructed OpenAI async client
        if AsyncOpenAI is not None:
            self._client: Optional[AsyncOpenAI] = AsyncOpenAI(
                api_key=settings.openai_api_key or None
            )
        else:
            self._client = None

    # Public ---------------------------------------------------------------

    async def run(
        self,
        messages: List[Dict[str, str]],
        citation_map: Dict[int, dict],
    ) -> Tuple[str, List[int], str]:
        scratchpad: List[str] = []
        last_observation: Optional[str] = None

        for step in range(cfg.MAX_STEPS):
            # For the first step, use the original messages
            # For subsequent steps, we'd need to modify the last user message to include scratchpad
            if step == 0:
                current_messages = messages
            else:
                # For now, just use original messages - proper ReAct loop would need more work
                current_messages = messages
                
            logger.debug("ReAct step %s with {} messages", step + 1, len(current_messages))

            llm_response = await self._llm_call(current_messages)

            action, argument = _parse_action(llm_response)

            if action == "Search":
                # For now we do a NO-OP retrieval and echo the argument; real retrieval
                # should be injected during integration tests.
                observation = f"(pretend search results for query: {argument})"
                scratchpad.append(f"Thought: The answer may be found in retrieved docs")
                scratchpad.append(f"Action: Search[{argument}]")
                scratchpad.append(f"Observation: {observation}")
                last_observation = observation
                continue

            if action == "Answer":
                # extract final answer text and type
                final_match = _FINAL_RE.search(llm_response)
                if final_match:
                    answer_type = final_match.group(1).lower()
                    answer_text = final_match.group(2).strip()
                else:
                    # fallback for old format or missing type
                    answer_type = "knowledge"
                    answer_text = argument or ""
                
                # Skip token-budget check for chitchat just like engine does
                if answer_type == "chitchat":
                    guarded_answer = apply_guardrails(answer_text, citation_map, None, answer_type=answer_type)
                else:
                    guarded_answer = apply_guardrails(answer_text, citation_map, messages, answer_type=answer_type)
                citation_indexes = _extract_citation_indexes(guarded_answer)
                return guarded_answer, sorted(citation_indexes), answer_type

        # If we exit loop without answer → refuse.
        return REFUSAL_MSG, [], "knowledge"

    # -------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------

    async def _llm_call(self, messages: List[Dict[str, str]]) -> str:
        """Single ChatCompletion call – kept overridable for tests."""
        if self._client is None:
            logger.warning("OpenAI client not available – returning dummy Answer")
            return "Thought: nothing to do\nAction: Answer\nFinal: I'm sorry, but I can't answer that question."

        # Prepare API request - use the structured messages directly
        api_request = {
            "model": settings.openai_chat_model,
            "temperature": self.temperature,
            "messages": messages  # ✅ Pass the structured messages array
        }
        
        logger.debug("=== REACT AGENT API CALL ===")
        logger.debug("Request: {}", json.dumps(api_request, indent=2))
        
        response = await self._client.chat.completions.create(**api_request)
        
        # Log the full response
        response_content = response.choices[0].message.content
        logger.debug("Response: {}", json.dumps({
            "model": response.model,
            "choices": [{
                "message": {
                    "role": response.choices[0].message.role,
                    "content": response_content
                },
                "finish_reason": response.choices[0].finish_reason
            }],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None
            }
        }, indent=2))
        logger.debug("=== END REACT AGENT API CALL ===")
        
        return response_content  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_action(llm_response: str) -> Tuple[str, str | None]:
    """Return (action, argument)."""
    match = _ACTION_RE.search(llm_response)
    if not match:
        return "Answer", llm_response  # assume model directly answered
    action = match.group(1)
    arg = match.group(2)
    return action, arg


def _extract_citation_indexes(text: str) -> List[int]:
    return [int(x) for x in re.findall(r"\[(\d+)\]", text)] 