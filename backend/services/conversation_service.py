"""Service for handling chat sessions and messages."""

from __future__ import annotations

import os
import uuid
from typing import Dict, Any, List, Optional

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.models import ChatSession, ChatMessage, MessageRole

_LOG_DB_MESSAGES = os.getenv("LOG_DB_MESSAGES", "").lower() in {"1", "true", "yes"}


async def get_or_create_session(session: AsyncSession, session_id: Optional[uuid.UUID] = None) -> ChatSession:
    """Get an existing chat session or create a new one."""
    if session_id:
        statement = select(ChatSession).where(ChatSession.id == session_id)
        result = await session.execute(statement)
        row = result.one_or_none()
        if row:
            chat_session = row[0]  # Unpack the ChatSession from the Row
            if _LOG_DB_MESSAGES:
                logger.debug("Found existing chat session: {}", chat_session.id)
            return chat_session

    # Create a new session if no ID was provided or if the ID was not found
    new_session = ChatSession()
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    logger.info("Created new chat session: {}", new_session.id)
    return new_session


async def get_session_history(session: AsyncSession, session_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Retrieve the message history for a given session."""
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    result = await session.execute(statement)
    messages = result.scalars().all()
    
    # Format for the agent's expected input
    history = [
        {"role": msg.role.value, "content": msg.content, "metadata": msg.metadata_}
        for msg in messages
    ]
    if _LOG_DB_MESSAGES:
        logger.debug("Retrieved {} messages for session {}", len(history), session_id)
    return history


async def add_message_to_session(
    session: AsyncSession,
    session_id: uuid.UUID,
    role: MessageRole,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChatMessage:
    """Add a new message to a chat session and save it to the database."""
    if _LOG_DB_MESSAGES:
        logger.debug(
            "Adding message to session {}: role={}, content_length={}",
            session_id,
            role.value,
            len(content),
        )

    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        metadata_=metadata or {},
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    if _LOG_DB_MESSAGES:
        logger.debug("Successfully saved message {}", message.id)
    return message
