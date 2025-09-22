"""Pydantic schemas used by the RAG core and (later) FastAPI layer."""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class Role(str, Enum):
    """OpenAI-compatible chat roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single message in the conversational history."""

    role: Role
    content: str

    model_config = ConfigDict(populate_by_name=True)


class ChatRequest(BaseModel):
    """Incoming request from client or tests."""

    history: List[ChatMessage] = Field(default_factory=list)
    prompt: str = Field(..., description="User question")
    session_id: Optional[UUID] = Field(default=None, description="Unique ID for the conversation session")


class ChatResponse(BaseModel):
    """Outgoing RAG answer."""

    answer: str
    citations: List[Dict[str, Any]]  # List of citation objects
    meta: Dict[str, Any] = Field(default_factory=dict)  # Optional metadata like mode, token usage
    session_id: UUID = Field(..., description="Unique ID for the conversation session") 