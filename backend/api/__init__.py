from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from backend.database import close_db

from .routes import router as api_router

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup logic (placeholder)
    yield
    # Shutdown: close DB engine/connection pool
    await close_db()


app = FastAPI(title="RAG-Unito Conversation API", lifespan=lifespan)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes under root (no prefix)
app.include_router(api_router)


# Optional root handler (not required but nice UX)
@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse({"status": "running", "name": "RAG-Unito API"}) 