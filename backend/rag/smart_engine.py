"""Smart Engine - Clean orchestration using the intelligent SmartAgent.

This replaces the complex engine.py with a much simpler flow:
User Query → SmartAgent → Decision to retrieve or not → Response

No more intent classification, no more prompt stuffing, just intelligent decision-making.
"""

from __future__ import annotations

from typing import List, Optional
import time
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from loguru import logger

from backend.models import MessageRole
from backend.rag.schemas import ChatMessage, ChatResponse
from backend.rag.agent import SmartAgent
from backend.services import conversation_service


async def chat(
    session: AsyncSession,
    user_query: str,
    history: List[ChatMessage],  # Kept for now, but will be deprecated
    session_id: Optional[UUID] = None,
) -> ChatResponse:
    """Stateful chat orchestrator using the SmartAgent and ConversationService."""
    
    # 1. Get or create a chat session
    is_new_session = not session_id
    chat_session = await conversation_service.get_or_create_session(session, session_id)
    session_id = chat_session.id

    # Log the start of the session if it's new
    if is_new_session:
         logger.info('component="chat" event_type="SESSION_START" session_id="{}"', str(session_id))
    
    turn_start = time.perf_counter()
    logger.info('component="chat" event_type="USER_QUERY" session_id="{}" query="{}"', str(session_id), user_query)

    # 2. Add the user's message to the database
    await conversation_service.add_message_to_session(
        session, session_id, MessageRole.USER, user_query
    )
    
    # 3. Load the true conversation history from the database
    history_from_db = await conversation_service.get_session_history(session, session_id)
    turn_id = sum(1 for msg in history_from_db if msg.get("role") == MessageRole.USER.value)
    logger.info(
        'component="chat" event_type="TURN_START" session_id="{}" turn_id={} messages={}',
        str(session_id),
        turn_id,
        len(history_from_db),
    )

    # 4. Call the agent to get the final answer
    agent = SmartAgent()
    final_answer, _, answer_type, agent_metadata = await agent.chat(
        session=session,
        history=history_from_db,
        user_query=user_query,
        session_id=session_id,
        turn_id=turn_id,
    )
    
    # 5. Save the agent's complete response to the database
    await conversation_service.add_message_to_session(
        session, session_id, MessageRole.ASSISTANT, final_answer, metadata=agent_metadata
    )

    elapsed_ms = int((time.perf_counter() - turn_start) * 1000)
    used_citations = agent_metadata.get("used_citations", [])
    retrieval_queries = agent_metadata.get("retrieval_queries", [])
    preview = final_answer[:200] + "..." if len(final_answer) > 200 else final_answer
    logger.info(
        'component="chat" event_type="ANSWER" session_id="{}" turn_id={} answer_type="{}" length={} preview="{}"',
        str(session_id),
        turn_id,
        answer_type,
        len(final_answer),
        preview,
    )
    logger.info(
        'component="chat" event_type="TURN_END" session_id="{}" turn_id={} answer_type="{}" length={} citations_used={} retrieval_queries={} latency_ms={}',
        str(session_id),
        turn_id,
        answer_type,
        len(final_answer),
        len(used_citations),
        len(retrieval_queries),
        elapsed_ms,
    )

    # 6. Format and return the final response to the client
    used_citations = agent_metadata.get("used_citations", [])
    citation_map = agent_metadata.get("citation_map", {})
    related_citations = agent_metadata.get("related_citations", [])
    citations = []
    for citation_num in used_citations:
        if citation_num in citation_map:
            citation_data = citation_map[citation_num]
            citations.append({
                "id": f"cite_{citation_num}",
                "title": citation_data.get("title", "Unknown Document"),
                "excerpt": citation_data.get("snippet", ""),
                "document_id": citation_data.get("document_id"),
                "sequence_number": citation_data.get("sequence_number"),
            })

    meta = {
        "mode": answer_type,
        "citation_map": citation_map,
        "used_citations": used_citations,
        "related_citations": related_citations,
    }
    
    return ChatResponse(
        answer=final_answer,
        citations=citations,
        meta=meta,
        session_id=session_id,
    ) 
