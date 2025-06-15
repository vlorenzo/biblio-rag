"""Pydantic schemas used by the RAG core and (later) FastAPI layer."""

from __future__ import annotations

from enum import Enum
from typing import List, Dict, Any
from uuid import UUID, uuid4

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

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class ChatRequest(BaseModel):
    """Incoming request from client or tests."""

    id: UUID = Field(default_factory=uuid4)
    history: List[ChatMessage] = Field(default_factory=list)
    prompt: str = Field(..., description="User question")


class ChatResponse(BaseModel):
    """Outgoing RAG answer."""

    request_id: UUID
    answer: str
    citations: Dict[int, Any]  # int index → arbitrary citation payload 