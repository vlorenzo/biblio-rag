"""Database models for the RAG application."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pathlib import Path

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel, Session
import sqlalchemy as sa


class DocumentClass(str, Enum):
    """Document classification types."""

    AUTHORED_BY_SUBJECT = "authored_by_subject"  # Works written by the subject
    SUBJECT_LIBRARY = "subject_library"  # Books the subject read
    ABOUT_SUBJECT = "about_subject"  # Works written about the subject
    SUBJECT_TRACES = "subject_traces"  # Fragments and traces left by the subject


class BatchStatus(str, Enum):
    """Batch processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Enumeration for the role of a message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# Base model with common fields
class BaseModel(SQLModel):
    """Base model with common fields."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel, table=True):
    """Document metadata model."""

    __tablename__ = "documents"

    title: str = Field(index=True)
    author: Optional[str] = Field(default=None, index=True)
    document_class: DocumentClass = Field(
        sa_column=Column(
            sa.Enum(DocumentClass, name="documentclass", values_callable=lambda obj: [e.value for e in obj]),
            nullable=False,
            index=True,
        )
    )
    publication_year: Optional[int] = Field(default=None, index=True)
    publisher: Optional[str] = Field(default=None)
    isbn: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    subject_tags: Optional[str] = Field(default=None)  # Comma-separated tags
    description: Optional[str] = Field(default=None)
    source_reference: Optional[str] = Field(default=None)
        
    # Additional bibliographic metadata as JSON
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    # Relationships
    content_files: List["ContentFile"] = Relationship(back_populates="document")
    chunks: List["Chunk"] = Relationship(back_populates="document")


class ContentFile(BaseModel, table=True):
    """Content file model."""

    __tablename__ = "content_files"

    document_id: UUID = Field(foreign_key="documents.id", index=True)
    filename: str = Field(index=True)
    file_path: str
    file_size: int
    checksum: str = Field(index=True)  # SHA-256 hash
    content_type: str  # txt, md, etc.

    # Relationships
    document: Document = Relationship(back_populates="content_files")


class Batch(BaseModel, table=True):
    """Batch processing model."""

    __tablename__ = "batches"

    name: str = Field(index=True)
    status: BatchStatus = Field(
        sa_column=Column(
            sa.Enum(BatchStatus, name="batchstatus", values_callable=lambda obj: [e.value for e in obj]),
            nullable=False,
            default=BatchStatus.PENDING,
            index=True,
        )
    )
    parameters: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))  # Chunking parameters
    total_documents: int = Field(default=0)
    processed_documents: int = Field(default=0)
    total_chunks: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    chunks: List["Chunk"] = Relationship(back_populates="batch")


class Chunk(BaseModel, table=True):
    """Text chunk model with embeddings."""

    __tablename__ = "chunks"

    document_id: UUID = Field(foreign_key="documents.id", index=True)
    batch_id: UUID = Field(foreign_key="batches.id", index=True)
    sequence_number: int = Field(index=True)  # Order within document
    text: str
    text_hash: str = Field(index=True)  # SHA-256 of cleaned text for caching
    token_count: int
    
    # Vector embedding (1536 dimensions for text-embedding-3-small)
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))
    
    # Chunk boundaries
    start_char: int = Field(default=0)
    end_char: int = Field(default=0)

    # Relationships
    document: Document = Relationship(back_populates="chunks")
    batch: Batch = Relationship(back_populates="chunks")


class ChatSession(SQLModel, table=True):
    """Represents a single conversation session."""
    __tablename__ = "chat_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    messages: List["ChatMessage"] = Relationship(back_populates="session")


class ChatMessage(SQLModel, table=True):
    """Represents a single message within a chat session."""
    __tablename__ = "chat_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)
    
    role: MessageRole = Field(
        sa_column=Column(
            sa.Enum(MessageRole, name="messagerole", values_callable=lambda obj: [e.value for e in obj]),
            nullable=False,
        )
    )
    content: str = Field(nullable=False)
    
    # Use metadata_ with a trailing underscore to avoid pydantic conflicts
    metadata_: Dict[str, Any] = Field(default={}, sa_column=Column(JSONB))
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    session: "ChatSession" = Relationship(back_populates="messages")


# Pydantic models for data preparation (in-memory)
class PreparedContentFile(SQLModel):
    """In-memory representation of a content file before DB save."""
    filename: str
    file_path: Path
    file_size: int
    checksum: str
    content_type: str

class PreparedChunk(SQLModel):
    """In-memory representation of a chunk before DB save."""
    text: str
    text_hash: str
    token_count: int
    start_char: int
    end_char: int


# Pydantic models for API
class DocumentCreate(SQLModel):
    """Document creation model."""

    title: str
    author: Optional[str] = None
    document_class: DocumentClass
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    language: Optional[str] = None
    subject_tags: Optional[str] = None
    description: Optional[str] = None
    source_reference: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentRead(SQLModel):
    """Document read model."""

    id: UUID
    title: str
    author: Optional[str]
    document_class: DocumentClass
    publication_year: Optional[int]
    publisher: Optional[str]
    isbn: Optional[str]
    language: Optional[str]
    subject_tags: Optional[str]
    description: Optional[str]
    source_reference: Optional[str]
    extra_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BatchCreate(SQLModel):
    """Batch creation model."""

    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BatchRead(SQLModel):
    """Batch read model."""

    id: UUID
    name: str
    status: BatchStatus
    parameters: Dict[str, Any]
    total_documents: int
    processed_documents: int
    total_chunks: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class ChunkRead(SQLModel):
    """Chunk read model."""

    id: UUID
    document_id: UUID
    batch_id: UUID
    sequence_number: int
    text: str
    token_count: int
    start_char: int
    end_char: int
    created_at: datetime 