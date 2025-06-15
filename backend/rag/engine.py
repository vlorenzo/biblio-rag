"""High-level glue function that orchestrates retrieval, prompt building,
ReAct agent execution, and guardrails.

This module purposefully keeps zero external deps (e.g. FastAPI) so it can be
imported from tests, CLI tools, or web routes.
"""

from __future__ import annotations

from typing import List, Tuple

from sqlmodel import Session
from loguru import logger

from backend.rag.schemas import ChatMessage, ChatResponse
from backend.rag.prompt import PromptBuilder
from backend.rag.agent import ReActAgent
from backend.rag.guardrails import apply_guardrails
from backend.services import retrieval_service as rs
from backend.config import settings


async def chat(
    session: Session,
    history: List[ChatMessage],
    user_query: str,
    top_k: int | None = None,
) -> ChatResponse:
    """Main chat orchestrator used by the upcoming FastAPI endpoint.

    Parameters
    ----------
    session : Session
        Active SQLModel session (async-friendly) to use for retrieval.
    history : List[ChatMessage]
        Previous chat history.
    user_query : str
        The new user message.
    top_k : int | None
        How many retrieval results to include. Defaults to settings.max_retrieval_results.
    """
    top_k = top_k or settings.max_retrieval_results

    # ------------------------------------------------------------------
    # 1. Retrieval
    # ------------------------------------------------------------------
    hits = await rs.retrieve_similar_chunks(session, user_query, k=top_k)

    # ------------------------------------------------------------------
    # 2. Prompt build
    # ------------------------------------------------------------------
    pb = PromptBuilder()
    system_prompt, messages, citation_map = pb.build(history, user_query, hits)

    # ------------------------------------------------------------------
    # 3. ReAct agent
    # ------------------------------------------------------------------
    agent = ReActAgent()
    answer, used_citations = await agent.run(messages, citation_map)

    # ------------------------------------------------------------------
    # 4. Final guardrails (token limit already handled inside agent)
    # ------------------------------------------------------------------
    final_answer = apply_guardrails(answer, citation_map, messages)

    logger.info("Chat answered with %s citations", len(used_citations))

    from uuid import uuid4

    selected_citations = {idx: citation_map[idx] for idx in used_citations if idx in citation_map}

    return ChatResponse(request_id=uuid4(), answer=final_answer, citations=selected_citations) 