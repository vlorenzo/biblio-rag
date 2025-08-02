# RAG Unito

A conversational AI system for bibliographic archives that enables natural language interaction with scholarly collections. Built as a research testbed for evaluating Retrieval-Augmented Generation (RAG) technologies in digital humanities and library science.

## Overview

RAG Unito transforms traditional archive search into intelligent conversation. Users can ask complex questions about historical collections and receive grounded, cited responses that reference primary sources. The system currently contains the Emanuele Artom bibliographic archive for research and evaluation.

### Key Capabilities

- **Intelligent Conversation Agent**: Uses OpenAI function calling to decide when to retrieve knowledge vs. respond conversationally
- **Citation Transparency**: Every response shows all consulted sources with full bibliographic metadata
- **Document Classification**: Handles authored works, personal library items, biographical materials, and historical traces
- **Vector Search Engine**: PostgreSQL with pgvector for semantic similarity search over document embeddings
- **Modern Web Interface**: React + TypeScript chat application with real-time conversation modes
- **Batch Document Ingestion**: CSV metadata parsing with automated text chunking and embedding generation

## Quick Start

**Prerequisites**: Python ≥ 3.12, Node.js ≥ 18, Docker, OpenAI API key

```bash
# 1. Clone and setup
git clone https://github.com/vlorenzo/biblio-rag.git
cd biblio-rag
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
uv sync

# 2. Start database
docker-compose -f docker-compose.dev.yml up -d postgres

# 3. Configure environment
cp env.example .env
# Edit .env with your OpenAI API key

# 4. Initialize database
uv run rag-ingest init-db

# 5. Ingest sample data
uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name "artom-collection"

# 6. Start application
uvicorn backend.api:app --reload &  # Backend
cd frontend && npm install && npm run dev  # Frontend
```

Open `http://localhost:3000` and start chatting with the archive!

## Documentation

- **[Getting Started](docs/getting-started.md)** - Detailed installation and deployment options
- **[User Guide](docs/user-guide.md)** - Using the chat interface and ingesting documents
- **[Architecture](docs/architecture.md)** - Technical implementation and system design

## Project Structure

```
├── backend/                 # Python FastAPI backend
│   ├── api/                # REST API routes and application
│   ├── rag/                # Conversation engine and agents
│   │   ├── agent/         # SmartAgent implementation
│   │   ├── guardrails/    # Response validation and safety
│   │   └── prompt/        # Prompt building utilities
│   ├── services/          # Business logic (ingestion, retrieval, embeddings)
│   ├── models.py          # SQLModel database schema
│   ├── config.py          # Configuration management
│   └── cli.py             # Command-line interface
├── frontend/               # React + TypeScript web application
│   └── src/
│       ├── components/    # React UI components
│       ├── hooks/         # Custom React hooks (useChat)
│       └── pages/         # Application pages
├── migrations/            # Alembic database migrations
├── source_data/          # Sample dataset (Emanuele Artom archive)
├── Dockerfile            # Multi-stage production build
├── docker-compose.yml    # Local development environment
└── ingest.py            # Standalone document ingestion script
```

## Technology Stack

**Backend**: FastAPI, SQLModel, PostgreSQL + pgvector, OpenAI APIs, Alembic  
**Frontend**: React, TypeScript, Tailwind CSS, Vite  
**AI**: OpenAI GPT-4 (chat), text-embedding-3-small (embeddings)  
**Infrastructure**: Docker, uv (package management)

## Current Status

**Production Ready Features:**
- Complete conversational interface with citation transparency
- Intelligent agent that detects conversation vs knowledge queries
- Vector search over 1536-dimensional embeddings
- Batch document ingestion with CSV metadata parsing
- Full-stack containerized deployment

**Sample Dataset:**
The Emanuele Artom bibliographic archive is included for testing and demonstrates the system's capabilities with real scholarly content.