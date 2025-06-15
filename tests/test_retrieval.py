import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.models import Document, Chunk, DocumentClass
from backend.services import retrieval_service as rs


@pytest_asyncio.fixture()
async def sample_data(db_session):
    """Insert one document + chunk with a known embedding (all zeros)."""
    doc = Document(
        id=uuid4(),
        title="Test doc",
        author="Unit Tester",
        document_class=DocumentClass.SUBJECT_LIBRARY,
    )
    db_session.add(doc)

    # 1536-dim zero vector
    embedding = [0.0] * 1536

    chunk = Chunk(
        document_id=doc.id,
        batch_id=uuid4(),
        sequence_number=0,
        text="dummy text",
        text_hash="hash",  # not relevant
        token_count=2,
        embedding=embedding,
        start_char=0,
        end_char=10,
    )
    db_session.add(chunk)
    await db_session.commit()
    await db_session.refresh(chunk)
    return chunk


@pytest.mark.asyncio
async def test_retrieve_similar_chunks(monkeypatch, db_session, sample_data):
    """Ensure retrieve_similar_chunks returns our sample chunk."""

    # Stub embedding service to return the zero vector
    class DummyEmbedder:
        def get_embedding(self, _):
            return [0.0] * 1536

    monkeypatch.setattr(rs, "get_embedding_service", lambda: DummyEmbedder())

    results = await rs.retrieve_similar_chunks(db_session, "any query", k=1)
    assert len(results) == 1
    chunk, distance = results[0]
    assert chunk.id == sample_data.id
    # distance should be ~0 for identical vectors
    assert distance == pytest.approx(0.0, abs=1e-6) 