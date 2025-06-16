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

    logger.debug("[chat] Starting chat orchestrator – history={} user_query=\"{}\"", len(history), user_query)

    # ------------------------------------------------------------------
    # 1. Retrieval
    # ------------------------------------------------------------------
    hits = await rs.retrieve_similar_chunks(session, user_query, k=top_k)
    logger.debug("[chat] Retrieved {} hits", len(hits))

    # ------------------------------------------------------------------
    # 2. Prompt build
    # ------------------------------------------------------------------
    pb = PromptBuilder()
    system_prompt, messages, citation_map = pb.build(history, user_query, hits)
    logger.debug("[chat] Prompt built – messages={} citations={}", len(messages), len(citation_map))

    # ------------------------------------------------------------------
    # 3. ReAct agent
    # ------------------------------------------------------------------
    agent = ReActAgent()
    answer, used_citations, answer_type = await agent.run(messages, citation_map)
    logger.debug("[chat] Agent run complete – answer_type={} used_citations={}", answer_type, used_citations)

    # ------------------------------------------------------------------
    # 4. Final guardrails (token limit already handled inside agent)
    #    For chitchat answers we skip the token-budget check because the
    #    system prompt may include large retrieval context that is irrelevant
    #    for a short courtesy reply, and we don't want to fail with
    #    TokenLimitError in that case.
    # ------------------------------------------------------------------
    if answer_type == "chitchat":
        final_answer = apply_guardrails(answer, citation_map, None, answer_type=answer_type)
    else:
        final_answer = apply_guardrails(answer, citation_map, messages, answer_type=answer_type)

    logger.debug("[chat] Guardrails applied – final_answer_len={} ", len(final_answer))

    logger.info("[chat] Answer ready with {} citations", len(used_citations))

    # Only include citations for knowledge answers
    if answer_type == "knowledge":
        selected_citations = [citation_map[idx] for idx in used_citations if idx in citation_map]
    else:
        selected_citations = []

    # Add conversation mode to metadata
    meta = {"mode": answer_type}

    logger.debug("[chat] Returning ChatResponse with {} citations", len(selected_citations))
    return ChatResponse(answer=final_answer, citations=selected_citations, meta=meta) 