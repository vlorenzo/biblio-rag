Immediate Next Milestones (Phase 4 kickoff)

1. Stabilise the test-suite (½ day)  
   ✅ Completed – parser fixed, DB tests conditionally skipped, coverage gate at 70 %.

2. Bootstrap Alembic migrations (½ day)  
   ✅ Completed – initial migration (`0001_initial`) + enums (`0002`, `0003`) applied, `init-db` wraps Alembic upgrade.

3. Conversation API ­– FastAPI skeleton (1 day)  
   a. `backend/api/__init__.py` with FastAPI app instance.  
   b. Pydantic I/O: reuse `ChatRequest` & `ChatResponse` from `backend.rag.schemas`.  
   c. Dependency-injected async DB session (`async_sessionmaker`).  
   d. POST `/chat` handler:  
      • parse request → call `engine.chat` → stream or return JSON.  
   e. Public `/healthz` and protected `/metrics`.

4. SSE / streaming support (½ day)  
   • Simple chunk-by-chunk Server-Sent Events generator around `engine.chat` (no fancy partial-token streaming yet).  
   • Toggle via query param `stream=true`.

5. Batch-monitoring endpoints (½ day)  
   • GET `/batches/` and `/batches/{id}` querying the existing `Batch` table.  
   • Add basic pagination & status filter.

6. Wire real retrieval into ReAct Agent (½ day)  
   • Implement `_search_callback` inside agent that calls `RetrievalService.search(...)` when `Action: Search[...]` is parsed.  
   • Update unit test with fake retrieval stub.

7. Integration tests (1 day)  
   • Fixture: launch Postgres in docker, apply migrations, load a tiny sample corpus.  
   • Test: POST `/chat` with a stubbed OpenAI client → expect grounded answer with citation ids.

8. Observability & security quick-win (¼ day)  
   • JWT auth dependency on ingestion routes & batch endpoints.  
   • Structured Loguru middleware for FastAPI.

9. Documentation touch-up (¼ day)  
   • Update README quick-start: docker-compose db, `uvicorn backend.api:app`.  
   • Add OpenAPI screenshot or link.

Execution order: 1 → 2 → 3 → 4/5 (parallel) → 6 → 7 → 8 → 9.

After this slice we'll have:  
• one-command DB bootstrap,  
• a functioning `/chat` HTTP endpoint powered by the new RAG core,  
• visibility into batch status,  
• green CI with Postgres + pgvector,  
ready for Phase 5 (optional frontend) and deployment work.

NOTE: Remaining items now start from step 3.