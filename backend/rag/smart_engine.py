"""Smart Engine - Clean orchestration using the intelligent SmartAgent.

This replaces the complex engine.py with a much simpler flow:
User Query → SmartAgent → Decision to retrieve or not → Response

No more intent classification, no more prompt stuffing, just intelligent decision-making.
"""

from __future__ import annotations

from typing import List

from sqlmodel import Session
from loguru import logger

from backend.rag.schemas import ChatMessage, ChatResponse
from backend.rag.agent import SmartAgent


async def chat(
    session: Session,
    history: List[ChatMessage],
    user_query: str,
) -> ChatResponse:
    """Simple chat orchestrator using the SmartAgent.
    
    The agent decides for itself when it needs to retrieve knowledge,
    making this much cleaner than the old intent classification approach.
    """
    logger.debug("[smart_engine] Starting chat – history={} user_query=\"{}\"", 
                len(history), user_query)
    
    # Convert ChatMessage objects to simple dict format for the agent
    history_dicts = [
        {"role": msg.role.value, "content": msg.content}
        for msg in history
    ]
    
    # Let the smart agent handle everything
    agent = SmartAgent()
    answer, used_citations, answer_type, citation_map = await agent.chat(
        session, history_dicts, user_query
    )
    
    logger.debug("[smart_engine] Agent response – answer_type={} citations={}", 
                answer_type, used_citations)
    
    # Build citation objects for the response
    citations = []
    for citation_num in used_citations:
        if citation_num in citation_map:
            citation_data = citation_map[citation_num]
            citations.append({
                "id": f"cite_{citation_num}",
                "title": citation_data.get("document_title", "Unknown Document"),
                "excerpt": "",  # We don't store excerpts in the citation map yet
                "document_id": citation_data.get("document_id"),
                "sequence_number": citation_data.get("sequence_number"),
                # Add other fields as needed
            })
    
    # Combine transparency data into meta
    meta = {
        "mode": answer_type,
        "citation_map": citation_map,
        "used_citations": used_citations,
    }

    return ChatResponse(
        answer=answer,
        citations=citations,
        meta=meta,
    ) 