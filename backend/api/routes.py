from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
from loguru import logger

from backend.database import get_session
from backend.config import settings
from backend.rag.schemas import ChatRequest, ChatResponse
from backend.rag import smart_engine as rag_engine

router = APIRouter()

# ---------------------------------------------------------------------------
# Metrics setup (minimal – one counter for requests)
# ---------------------------------------------------------------------------
request_counter = Counter("api_requests_total", "Total API requests", ["endpoint", "method", "status"])


# ---------------------------------------------------------------------------
# Healthz
# ---------------------------------------------------------------------------


@router.get("/healthz", response_class=JSONResponse, tags=["health"])
async def healthz() -> JSONResponse:
    request_counter.labels("/healthz", "GET", "200").inc()
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Metrics (optional bearer-token protected)
# ---------------------------------------------------------------------------


@router.get("/metrics", response_class=PlainTextResponse, tags=["metrics"])
async def metrics(authorization: str | None = Header(default=None)) -> PlainTextResponse:  # noqa: D401
    # If a token is configured we require Authorization header.
    token = settings.metrics_token
    if token is not None:
        if authorization is None or not authorization.startswith("Bearer "):
            request_counter.labels("/metrics", "GET", "401").inc()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        supplied = authorization.removeprefix("Bearer ")
        if supplied != token:
            request_counter.labels("/metrics", "GET", "401").inc()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    request_counter.labels("/metrics", "GET", "200").inc()
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Main conversational endpoint."""
    try:
        response = await rag_engine.chat(
            session=session,
            user_query=request.prompt,
            history=request.history,
            session_id=request.session_id,
        )
        request_counter.labels("/chat", "POST", "200").inc()
        return response
    except Exception as exc:  # pylint: disable=broad-except
        # Re-raise as 500 so client gets JSON error.
        logger.exception("[chat_endpoint] Unhandled exception", exc_info=True)
        request_counter.labels("/chat", "POST", "500").inc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc 