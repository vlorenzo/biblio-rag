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
from sqlalchemy import select, cast, Float
from sqlalchemy.sql import text
from sqlmodel import Session
import sqlalchemy as sa
from sqlalchemy.orm import selectinload

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

    # Cast the vector distance to a plain Float so pgvector/SQLAlchemy don't try
    # to treat it as another vector.
    distance_expr = cast(Chunk.embedding.op("<->")(emb_param), Float).label("distance")

    stmt = (
        select(Chunk, distance_expr)
        .join(Document, Document.id == Chunk.document_id)
        .options(selectinload(Chunk.document))  # eager-load to avoid async lazy-load later
        .order_by("distance")
        .limit(k)
    )

    if document_class is not None:
        stmt = stmt.where(Document.document_class == document_class)

    if min_score is not None:
        stmt = stmt.where(distance_expr <= min_score)

    # NOTE: Depending on the SQLAlchemy version / DB driver combination the
    # rows returned by `session.execute` can be either:
    #   1. sqlalchemy.engine.Row / RowMapping  – supports attribute access
    #      (e.g. `row.distance`) **and** positional access (`row[0]`).
    #   2. A plain tuple `(chunk, distance)` when using the async pg driver.
    #   3. In very old versions, a single scalar (distance) if the ORM entity
    #      failed to be included in the SELECT list (edge-case we observed in
    #      production).
    # To avoid brittle positional access we explicitly unpack the tuple when
    # possible and fall back to attribute access.  Any row that doesn't match
    # the expected structure will be skipped with a warning rather than
    # crashing the whole request.

    result = await session.execute(stmt)
    rows = result.all()

    hits: List[Tuple[Chunk, float]] = []
    for row in rows:
        try:
            # ------------------------------------------------------------------
            # Common cases first: tuple / list / RowMapping (sequence-like)
            # ------------------------------------------------------------------
            if isinstance(row, (tuple, list)):
                if len(row) < 2:
                    # Not enough elements – skip
                    continue
                chunk, distance = row[0], row[1]
            # sqlalchemy.engine.Row / RowMapping behaves like a mapping – use keys
            elif hasattr(row, "_mapping"):
                # RowMapping gives us attribute access (row.distance) and mapping
                chunk = row[0]  # type: ignore[index]
                distance = row.distance  # type: ignore[attr-defined]
            # Edge-case: some drivers may give a single scalar (distance)
            # which is useless for our purposes → skip without error.
            else:
                logger.debug(
                    "[retrieval_service] Received unexpected scalar row (%s) – skipping",
                    type(row),
                )
                continue

            # ------------------------------------------------------------------
            # Basic sanity check before appending
            # ------------------------------------------------------------------
            if chunk is None or not isinstance(chunk, Chunk) or not isinstance(distance, (int, float)):
                continue

            hits.append((chunk, float(distance)))
        except Exception as ex:  # pragma: no cover – defensive guard
            logger.warning("[retrieval_service] Skipping invalid row in similarity query: %s", ex)

    return hits


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