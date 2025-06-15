"""Vector similarity retrieval service using pgvector.

This module exposes two helper functions:

1. `search_similar_chunks`   – low-level similarity query that returns Chunk
   objects ordered by distance.
2. `retrieve_similar_chunks` – high-level helper that takes plain text,
   generates its embedding (via embedding_service) and runs the search.

Both helpers are asynchronous and rely on pgvector's `<->` cosine distance
operator.  The service is intentionally lightweight: it performs the SELECT
only, delegating post-processing (deduping, formatting) to the caller.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from loguru import logger
from sqlalchemy import select
from sqlalchemy.sql import text
from sqlmodel import Session

from backend.models import Chunk, Document
from backend.services.embedding_service import get_embedding_service

# ---------------------------------------------------------------------------
# Low-level search
# ---------------------------------------------------------------------------


async def search_similar_chunks(
    session: Session,
    query_embedding: List[float],
    k: int = 5,
    min_score: Optional[float] = None,
    document_class: Optional[str] = None,
) -> List[Tuple[Chunk, float]]:
    """Return top-k chunks ordered by cosine distance.

    Parameters
    ----------
    session : AsyncSession
        Active DB session.
    query_embedding : List[float]
        1536-dimensional embedding produced with the same model used for corpus.
    k : int, default 5
        Number of results to return.
    min_score : float | None
        If provided, filter out results whose similarity score is above this
        threshold (remember: cosine distance → 0 means identical).
    document_class : str | None
        Optional filter on Document.document_class.
    """
    # pgvector uses lists – convert to Python list of floats to JSON parameter.
    emb_param = query_embedding

    distance_expr = Chunk.embedding.op("<->")(emb_param)

    stmt = (
        select(Chunk, distance_expr.label("distance"))
        .join(Document, Document.id == Chunk.document_id)
        .order_by("distance")
        .limit(k)
    )

    if document_class is not None:
        stmt = stmt.where(Document.document_class == document_class)

    if min_score is not None:
        stmt = stmt.where(distance_expr <= min_score)

    result = await session.execute(stmt)
    rows = result.all()
    return [(row[0], float(row.distance)) for row in rows]  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# High-level helper
# ---------------------------------------------------------------------------


async def retrieve_similar_chunks(
    session: Session,
    query_text: str,
    k: int = 5,
    min_score: Optional[float] = None,
    document_class: Optional[str] = None,
) -> List[Tuple[Chunk, float]]:
    """Embed plain text and return similar chunks with distances."""
    embedder = get_embedding_service()

    logger.debug("Generating embedding for query text (length = %s)", len(query_text))
    query_emb = embedder.get_embedding(query_text)

    logger.debug("Running similarity search on chunks …")
    return await search_similar_chunks(session, query_emb, k, min_score, document_class) 