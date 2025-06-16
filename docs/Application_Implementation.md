# RAG Unito - Current Implementation Status

## Overview

RAG Unito is a **work-in-progress** conversational application for bibliographic corpus analysis. This document reflects the **actual current state** of implementation, not planned features.

## ✅ **Actually Implemented Components**

### **1. Project Structure & Configuration**
- ✅ **pyproject.toml**: Complete project configuration with dependencies
- ✅ **Environment configuration**: `env.example` with all required variables
- ✅ **Development tools**: Black, Ruff, MyPy, pre-commit configuration
- ✅ **Docker setup**: `docker-compose.dev.yml` for PostgreSQL
- ✅ **Git configuration**: `.gitignore` and `.pre-commit-config.yaml`

### **2. Database Models (SQLModel)**
- ✅ **Complete schema**: Documents, ContentFiles, Chunks, Batches models in `backend/models.py`
- ✅ **pgvector integration**: Vector field for embeddings
- ✅ **Alembic setup**: Basic configuration in `alembic.ini` and `migrations/env.py`
- ✅ **Database migrations**: Initial schema and enum revisions present (`0001`, `0002`, `0003`).

### **3. Core Services**
- ✅ **CSV Parser** (`backend/services/csv_parser.py`): 
  - Auto-detects document types from filenames
  - Maps CSV columns to database schema
  - Handles encoding detection and data cleaning
- ✅ **Text Chunker** (`backend/services/text_chunker.py`):
  - Multiple chunking strategies (sliding window, paragraph-based)
  - Smart boundary detection
  - Content hashing for deduplication
- ✅ **Embedding Service** (`backend/services/embedding_service.py`):
  - OpenAI API integration
  - Async processing with rate limiting
  - Error handling and retry logic
- ✅ **Ingestion Service** (`backend/services/ingestion_service.py`):
  - Orchestrates the full pipeline
  - Batch management and progress tracking
  - Database operations
- ✅ **Retrieval Service** (`backend/services/retrieval_service.py`):
  - Vector similarity search using pgvector `<->` operator
  - Auto-created HNSW index for fast cosine search
  - Helper to embed query and return top-k chunks with document metadata

### **4. RAG Core (UPDATED)**
- ✅ **Prompt Builder** (`backend/rag/prompt/builder.py`) – builds inline-tagged context with citation map + conversation mode instructions.
- ✅ **Guardrails** (`backend/rag/guardrails/*`) – token limit + citation validation + chitchat constraints + safe refusal.
- ✅ **ReAct Agent** (`backend/rag/agent/react_agent.py`) – lightweight ReAct loop with conversation mode detection (chitchat vs knowledge).
- ✅ **Chat Orchestrator** (`backend/rag/engine.py`) – ties together retrieval, prompt builder, agent and guardrails with mode-aware citation handling.
- ✅ **Conversation Modes** – Agent can distinguish between chitchat (greetings, brief social) and knowledge queries (factual questions requiring citations).
- ✅ **Enhanced Tests** (`tests/test_react_agent.py`) – covers both conversation modes.

### **5. Conversation API (NEW)**
- ✅ **FastAPI Application** (`backend/api/__init__.py`) – main app with lifespan management for database cleanup
- ✅ **API Routes** (`backend/api/routes.py`) – three endpoints with proper error handling:
  - `GET /healthz` – health check endpoint
  - `GET /metrics` – Prometheus metrics with optional bearer token protection  
  - `POST /chat` – main conversational endpoint using RAG engine
- ✅ **Prometheus Integration** – request counting and standard Python metrics
- ✅ **Configuration** – added `metrics_token` setting for optional endpoint protection
- ✅ **Dependencies** – added `prometheus-client>=0.19.0` to `pyproject.toml`

### **6. CLI Interface**
- ✅ **Typer-based CLI** (`backend/cli.py`) with commands:
  - `rag-ingest ingest` - Ingest documents from CSV metadata file.
  - `rag-ingest status` - Check batch status
  - `rag-ingest list-batches` - List all batches
  - `rag-ingest init-db` - Initialize database tables

### **7. Testing Infrastructure**
- ✅ **Basic unit tests**:
  - `tests/test_csv_parser.py` - CSV parsing tests
  - `tests/test_models.py` - Database model tests (require PostgreSQL)
  - `tests/test_retrieval.py` - Vector similarity search tests (require PostgreSQL)
  - `tests/test_prompt_builder.py` - Prompt building smoke test (no DB)
  - `tests/test_guardrails.py` - Guardrails smoke test
  - `tests/test_react_agent.py` - ReAct agent smoke test (OpenAI stubbed)
  - `tests/conftest.py` - Test configuration
- ✅ **Test script**: `test_ingestion.py` - Manual testing of CSV parsing and chunking

## ❌ **NOT Implemented (Despite Documentation)**

### **Missing Core Components**
- ❌ **No Git Repository**: Code exists only locally, never pushed to any repo
- ❌ **No Database Migrations**: Alembic configured but no actual migration files
- ✅ **Database Initialization**: `init-db` runs Alembic upgrade and succeeds
- ❌ **No End-to-End Testing**: ingestion → retrieval → chat still untested with live DB & OpenAI
- ✅ **FastAPI Endpoints**: Web API implemented with `/healthz`, `/metrics`, and `/chat` endpoints
- ❌ **No Frontend**: No web interface

### **Untested Functionality**
- ❌ **OpenAI Integration**: Embedding service and ReAct agent call rely on API key; only stubbed in tests
- ✅ **Metadata Ingestion**: Ingest script loads CSV metadata; chunk/embedding path pending text files

## 🔧 **What Actually Works (Verified)**

### **New Conversation Modes (June 2025)**
The system now supports intelligent conversation management:

**Chitchat Mode:**
- Handles greetings, thanks, farewells politely
- Responses are brief and redirect to the collection scope
- No citations required or allowed
- Example: "Hi!" → "Hi! How can I help you with the Emanuele Artom collection?"

**Knowledge Mode:**
- Handles factual questions about the bibliographic corpus
- Requires citations for all factual claims
- Falls back to safe refusal if no sources available
- Example: "Who was Artom?" → Answer with [1] citations or refusal

**Guardrails:**
- Chitchat responses cannot contain citations or be too long
- Knowledge responses must have valid citations
- Out-of-scope questions get polite refusal

### **Standalone Components**
These components should work independently:

1. **CSV Parsing**: 
   ```python
   from backend.services.csv_parser import CSVMetadataParser
   parser = CSVMetadataParser()
   documents, errors = parser.parse_csv("source_data/inventario_Artom_Prandi.csv")
   ```

2. **Text Chunking**:
   ```python
   from backend.services.text_chunker import TextChunker
   chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
   chunks = chunker.chunk_text("Your text here")
   ```

3. **Test Script**:
   ```bash
   python test_ingestion.py
   ```

4. **Conversation API** (NEW):
   ```bash
   # Start the API
   uvicorn backend.api:app --reload
   
   # Test endpoints
   curl http://127.0.0.1:8000/healthz
   curl http://127.0.0.1:8000/metrics
   curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"prompt":"Hello","history":[]}'
   ```

## 📁 **Actual Project Structure**

```
rag-unito/
├── backend/
│   ├── __init__.py
│   ├── cli.py                 # CLI commands (untested)
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection setup
│   ├── models.py              # SQLModel schemas
│   ├── api/                   # ✅ NEW: FastAPI application
│   │   ├── __init__.py        # FastAPI app with lifespan management
│   │   └── routes.py          # API endpoints (/healthz, /metrics, /chat)
│   ├── rag/                   # ✅ RAG core components
│   │   ├── schemas.py         # ChatRequest/ChatResponse models
│   │   ├── engine.py          # Chat orchestrator
│   │   ├── agent/             # ReAct agent implementation
│   │   ├── prompt/            # Prompt builder
│   │   └── guardrails/        # Response validation
│   └── services/
│       ├── __init__.py
│       ├── csv_parser.py      # ✅ CSV parsing logic
│       ├── text_chunker.py    # ✅ Text chunking logic
│       ├── embedding_service.py # ✅ OpenAI integration
│       ├── retrieval_service.py # ✅ Vector similarity search
│       └── ingestion_service.py # ✅ Pipeline orchestration
├── docs/
│   ├── PRD.md
│   ├── Implementation_Plan.md
│   ├── Application_Implementation.md # This document
│   └── MacOS_Setup_Guide.md
├── tests/
│   ├── conftest.py           # Test configuration
│   ├── test_models.py        # Basic model tests
│   └── test_csv_parser.py    # CSV parser tests
├── migrations/
│   ├── env.py               # Alembic environment
│   └── script.py.mako       # Migration template
├── source_data/             # CSV files provided by user
├── pyproject.toml           # ✅ Project configuration
├── alembic.ini             # ✅ Migration configuration
├── docker-compose.dev.yml  # ✅ PostgreSQL setup
├── env.example             # ✅ Environment variables
├── test_ingestion.py       # ✅ Manual test script
├── .gitignore              # ✅ Git configuration
├── .pre-commit-config.yaml # ✅ Code quality hooks
└── README.md               # Basic project info
```

## 🚨 **Critical Missing Pieces**

### **1. Database Setup**
- **Solved**: Alembic migrations added; `init-db` succeeds against fresh Postgres

### **2. Git Repository**
- **Problem**: No remote repository exists
- **Impact**: Cannot clone or collaborate
- **Status**: Code exists only locally

### **3. End-to-End Testing**
- **Problem**: Full pipeline never tested
- **Impact**: Unknown if ingestion actually works
- **Status**: Individual components implemented but integration untested

### **4. OpenAI API Integration**
- **Problem**: API calls implemented but never tested
- **Impact**: Embedding generation may fail
- **Status**: Code exists but requires API key and testing

## 🔍 **What Can Be Tested Right Now**

### **1. CSV Parsing (Standalone)**
```bash
python test_ingestion.py
```
This should work and test CSV parsing with your actual data files.

### **2. Conversation API (NEW)**
```bash
# Start the API
uvicorn backend.api:app --reload

# In another terminal, test endpoints:
curl http://127.0.0.1:8000/healthz                    # Should return {"status":"ok"}
curl http://127.0.0.1:8000/metrics                    # Should return Prometheus metrics
curl -X POST http://127.0.0.1:8000/chat \
     -H 'Content-Type: application/json' \
     -d '{"prompt":"Hello","history":[]}'              # Should return ChatResponse JSON
```

### **3. Individual Service Components**
```python
# Test CSV parsing
from backend.services.csv_parser import CSVMetadataParser
parser = CSVMetadataParser()
docs, errors = parser.parse_csv("source_data/inventario_Artom_Prandi.csv")
print(f"Parsed {len(docs)} documents with {len(errors)} errors")

# Test text chunking
from backend.services.text_chunker import TextChunker
chunker = TextChunker()
chunks = chunker.chunk_text("Sample text for testing")
print(f"Created {len(chunks)} chunks")
```

### **4. Configuration Loading**
```python
from backend.config import get_settings
settings = get_settings()
print(f"Database URL: {settings.database_url}")
```

## 📋 **TODO: Critical Next Steps**

### **Phase 1: Make Current Code Actually Work**
1. **Create actual database migrations**
   - Generate initial migration from models
   - Test database creation
   - Verify pgvector extension setup

2. **Test CLI commands**
   - Set up test database
   - Test `init-db` command
   - Test ingestion with sample data

3. **Verify OpenAI integration**
   - Test API connectivity
   - Test embedding generation
   - Handle rate limits and errors

4. **End-to-end testing**
   - Test full ingestion pipeline
   - Verify data is stored correctly
   - Test batch management

### **Phase 2: Complete Missing Infrastructure**
1. **Create Git repository**
   - Initialize repository
   - Push existing code
   - Set up proper branching

2. **Improve testing**
   - Add integration tests
   - Test database operations
   - Mock OpenAI API for testing

3. **Documentation cleanup**
   - Remove aspirational features
   - Document actual setup process
   - Create realistic usage examples

### **Phase 3: Implement Missing Features** (updated → now Phase 4 in master plan)
1. **FastAPI `/chat` endpoint** integrating `backend.rag.engine.chat` with live DB session
2. **Streaming SSE support & JSON schema validation**
3. **Thin Frontend** (optional)
4. **End-to-End integration tests** (live DB + mocked OpenAI)

## 🎯 **Realistic Current Capabilities**

**What you can do right now:**
- Parse CSV files and extract metadata
- Chunk text content with different strategies
- Run vector similarity search via Retrieval Service
- Build prompts, enforce guardrails, run a ReAct reasoning loop in-memory (with stubbed LLM) and receive grounded answers
- **Start a complete HTTP API** with health checks, metrics, and chat endpoints
- **Test conversational interactions** via HTTP requests (returns safe refusal when no content is ingested)

**What you cannot do yet:**
- Actually ingest documents into a database (pending migrations/CLI init-db)
- Generate embeddings (requires OpenAI API key and testing)
- Have meaningful conversations (requires ingested document content with embeddings)
- Deploy or run the application in production

This document reflects the honest current state of the project as of the last implementation session. 

✅ **Standalone ingestion script** `ingest.py` (root del progetto):
  esegue l'ingestione batch con un solo event-loop e ha superato il test
  completo senza errori `greenlet_spawn`.

  ```bash
  uv run python ingest.py source_data/your.csv --no-chunking --batch-name demo
  ```

  Rimane l'interfaccia consigliata per tutte le operazioni di import. 