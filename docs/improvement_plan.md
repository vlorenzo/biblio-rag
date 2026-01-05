# Improvement Plan: SmartAgent-Only RAG

## Goals
- Remove legacy ReAct/intent code paths and keep a single SmartAgent orchestration path.
- Keep prompt templates as external `.txt` files, but clarify a single prompt registry workflow.
- Improve logging structure for readability while preserving high detail.
- Improve citation management for clarity across multi-turn conversations without heavy enforcement.

## Scope
- Backend: `backend/rag`, `backend/services`, `backend/api/routes.py` references.
- Docs: architecture and prompt registry docs.
- No changes to SQL safety enforcement, token guardrails, or UX labels (explicitly out of scope).

## Proposed Changes

### 1) Consolidate to SmartAgent-only flow
- Remove unused legacy modules:
  - `backend/rag/engine.py`
  - `backend/rag/agent/react_agent.py`
  - `backend/rag/intent.py`
  - `backend/rag/prompt/builder.py`
  - `backend/rag/prompt/templates/intent_classifier.txt`
  - `backend/rag/prompt/templates/system_prompt_inline.txt`
- Update exports in `backend/rag/__init__.py` to point to SmartEngine.
- Update docs referencing legacy ReAct/intent or inline prompt builder.

### 2) Prompt registry cleanup
- Keep `backend/rag/prompt/templates/*.txt` as the source of truth.
- Update `backend/rag/prompt/templates/README.md` to list only SmartAgent templates and usage.
- Ensure SmartAgent always loads from registry; keep fallback only for safety.

### 3) Logging readability
- Standardize key log events in SmartAgent:
  - `USER_QUERY`, `AGENT_DECISION`, `RETRIEVAL`, `SQL_QUERY`, `SYNTHESIS`, `FINAL_RESPONSE`.
- Remove repeated or redundant log statements and keep concise previews.
- Keep trace logs but grouped by event type.

### 4) Citation handling (clean but minimal)
- Track and store used citations and citation map in SmartAgent metadata (already logged, but not persisted in `meta`).
- For multi-turn chat, include prior tool citations only if referenced in the answer; avoid auto-including unrelated sources.
- Keep current citation validation (missing index errors), no additional enforcement.

## Compatibility Notes
- API endpoints keep using `smart_engine.chat`.
- No schema changes.
- No change in retrieval parameters.

## Rollout Steps
1. Remove legacy modules and update imports/exports.
2. Update docs and prompt registry README.
3. Refactor SmartAgent logging and metadata packaging.
4. Run unit tests (if available).

