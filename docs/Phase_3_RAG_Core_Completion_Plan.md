# Phase 3 – RAG Core Completion

> Status: **Planned**
>
> Goal – deliver a minimal but production-grade RAG loop that:
> 1. Receives chat history + user query
> 2. Decides whether to retrieve, and if so executes `RetrievalService.search()`
> 3. Builds a prompt that encodes `document_class` semantics
> 4. Calls the LLM, returning a grounded answer **with citations** (or a safe refusal)
> 5. Enforces hard limits on tokens, citations, and style via guardrails

---

## 1  Code-base Skeleton

```
backend/
└── rag/
    ├── agent/          # ReAct wrapper & tools
    ├── prompt/         # PromptBuilder util
    ├── guardrails/     # safety & validation helpers
    └── schemas.py      # ChatRequest/ChatResponse (used later by API)
```

*Each sub-folder gets an `__init__.py` and is re-exported in `backend/__init__.py`.*

---

## 2  PromptBuilder (`backend/rag/prompt/builder.py`)

Responsibilities

* Accept `List[(Chunk, distance, Document)]` and chat history
* Apply either **inline tag** or **sectioned** template (config flag, default = inline)
* Annotate each chunk with `document_class` (**primary**, **trace**, **library**, **about**)
* Return
  * `system_prompt` (`str`)
  * `messages` (`List[dict]`) – OpenAI chat format
  * `citation_map` (`Dict[int, ChunkMetadata]`)

Steps
1. Encode label → rules constants from `Prompt_Builder_Design_Notes.md`.
2. Helper `_label_chunk(doc_class)`.
3. Token-budget helper: trim chunks until prompt ≤ `MAX_CONTEXT_TOKENS – safety_margin`.
4. Tests `tests/test_prompt_builder.py` verifying labels & trimming logic.

---

## 3  ReAct Agent Wrapper (`backend/rag/agent/react_agent.py`)

### 3.1  Tools
* `SearchTool` – async wrapper around `RetrievalService.search()`.
* `LLMTool` – OpenAI ChatCompletion wrapper with retry/back-off.

### 3.2  Planner Loop (simplified)
```python
while step < MAX_STEPS:
    prompt = build_react_prompt(history, scratchpad, latest_observation)
    result = LLMTool.call(prompt)
    if result["action"] == "Search":
        observation = SearchTool.run(result["argument"])
        scratchpad.append((result, observation))
    elif result["action"] == "Answer":
        return result["answer"], result["citations"]
```

### 3.3  Parsing Strategy
* Lightweight regex on model output (e.g. `Action: Search["..."]`).
* Guardrails refuse if pattern not respected.

### 3.4  Config (`backend/rag/agent/config.py`)
```
MAX_STEPS     = 4
TEMPERATURE   = 0.2
SEARCH_TOP_K  = 4
```

---

## 4  Guardrails Module (`backend/rag/guardrails/`)

| File | Purpose |
|------|---------|
| `token_utils.py` | Count tokens via `tiktoken`; enforce context limit. |
| `citation.py`   | Validate that every `[n]` in answer exists in `citation_map`. |
| `policy.py`     | Central `apply_guardrails()` – token check, citation check, refusal fallback. |
| `errors.py`     | Custom exceptions (`TokenLimitError`, `CitationError`, …). |

Constant:
```python
REFUSAL_MSG = "I'm sorry, but I can't answer that question."
```

---

## 5  Glue Function – Chat Engine (`backend/rag/engine.py`)

```python
async def chat(history: List[ChatMessage], user_query: str) -> ChatResponse:
    # 1 Retrieve
    hits = await RetrievalService.search(user_query, top_k=SEARCH_TOP_K)
    # 2 Prompt build
    pb = PromptBuilder()
    system_prompt, messages, citation_map = pb.build(history, user_query, hits)
    # 3 ReAct agent
    agent = ReActAgent()
    answer, used_citations = await agent.run(messages, citation_map)
    # 4 Guardrails
    final_answer = Guard.apply(answer, used_citations, hits)
    return ChatResponse(answer=final_answer, citations=used_citations)
```

The function will be imported by the FastAPI `/chat` route in Phase 4.

---

## 6  Testing Strategy

```
tests/
└── test_agent.py
```

1. Patch `openai.ChatCompletion.acreate` to return scripted responses.
2. Provide in-memory fake `RetrievalService` returning two chunks with different `document_class` values.
3. Assert:
   * Agent returns an answer containing citations.
   * Guardrails do not raise.
   * Token limit holds for long history.

---

## 7  Implementation Order

1. **PromptBuilder** (+ tests)
2. **Guardrails** helpers
3. **ReAct agent** (happy-path) with stubbed OpenAI & retrieval
4. Integrate into `engine.chat`
5. Expand tests to negative paths (missing citations, over-tokens)
6. Wire refusal fallback; aim for ≥ 90 % coverage for new modules

---

## 8  Prompt Template Notes

* Implement **inline tagging** first (simpler, safe).  
* Keep template selection flag (defaults to inline) for future "sectioned" version.
* Embed instruction block from design notes in `system_prompt` verbatim.
* Defer `authored_by_subject` boosting until we gather retrieval metrics.

---

## 9  Dependencies

Add to `pyproject.toml` if missing:
* `tiktoken`
* `python-dotenv` (for local dev convenience)

---

## 10  Done ≠ Shipped

The loop is **ready for production** only after:
* FastAPI `/chat` endpoint exposes it (Phase 4)
* JWT auth & observability middle-ware wired
* CI passes end-to-end integration test (ingest → chat) 