"""RAG Core package.

This sub-package groups together the higher-level retrieval-augmented-generation
components (prompt building, guardrails, reactive agent, glue engine).
All modules are kept intentionally lightweight and import-safe so that they can
be used independently from the FastAPI layer.
"""

from importlib import import_module

# Re-export high-level helpers so callers can simply do `from backend.rag import chat`.

_engine = import_module("backend.rag.engine")
chat = _engine.chat  # type: ignore[attr-defined]

__all__ = [
    "chat",
] 