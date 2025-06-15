"""Test database models."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Document, DocumentClass, Batch, BatchStatus


@pytest.mark.asyncio
async def test_create_document(db_session: AsyncSession):
    """Test document creation."""
    document = Document(
        title="Test Document",
        author="Test Author",
        document_class=DocumentClass.AUTHORED_BY_SUBJECT,
        publication_year=2023,
        description="A test document",
    )
    
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    assert document.id is not None
    assert document.title == "Test Document"
    assert document.author == "Test Author"
    assert document.document_class == DocumentClass.AUTHORED_BY_SUBJECT
    assert document.publication_year == 2023
    assert document.created_at is not None
    assert document.updated_at is not None


@pytest.mark.asyncio
async def test_create_batch(db_session: AsyncSession):
    """Test batch creation."""
    batch = Batch(
        name="Test Batch",
        parameters={"chunk_size": 500, "overlap": 50},
        total_documents=10,
    )
    
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)
    
    assert batch.id is not None
    assert batch.name == "Test Batch"
    assert batch.status == BatchStatus.PENDING
    assert batch.parameters == {"chunk_size": 500, "overlap": 50}
    assert batch.total_documents == 10
    assert batch.processed_documents == 0
    assert batch.created_at is not None


@pytest.mark.asyncio
async def test_document_class_enum():
    """Test document class enumeration."""
    assert DocumentClass.AUTHORED_BY_SUBJECT == "authored_by_subject"
    assert DocumentClass.SUBJECT_LIBRARY == "subject_library"
    assert DocumentClass.ABOUT_SUBJECT == "about_subject"
    assert DocumentClass.SUBJECT_TRACES == "subject_traces"


@pytest.mark.asyncio
async def test_batch_status_enum():
    """Test batch status enumeration."""
    assert BatchStatus.PENDING == "pending"
    assert BatchStatus.PROCESSING == "processing"
    assert BatchStatus.COMPLETED == "completed"
    assert BatchStatus.FAILED == "failed" 