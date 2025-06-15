# RAG Unito

A lightweight, production-ready conversational application that combines Large-Language-Model (LLM) reasoning with reliable Retrieval-Augmented Generation (RAG) over a curated bibliographic corpus.

## Features

- **Document Ingestion**: Excel-based metadata with text file processing
- **Flexible Chunking**: Configurable text chunking or full-document embedding
- **Vector Search**: PostgreSQL with pgvector for efficient similarity search
- **ReAct Agent**: Intelligent retrieval decisions using OpenAI function calling
- **Bibliographic Rigor**: Proper metadata handling for academic/archival sources
- **Production Ready**: Async FastAPI, structured logging, comprehensive testing

## Quick Start

### Prerequisites

- Python ≥ 3.12
- PostgreSQL ≥ 16 with pgvector extension
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rag-unito
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
# Start PostgreSQL and create database
createdb rag_unito

# Run migrations
alembic upgrade head
```

### Usage

#### Document Ingestion

```bash
# Ingest documents with chunking
rag-ingest ingest metadata.xlsx --chunk-size 500 --chunk-overlap 50

# Ingest full documents without chunking
rag-ingest ingest metadata.xlsx --no-chunking

# Check batch status
rag-ingest status --batch-id <batch-id>
```

#### API Server

```bash
# Start the API server
uvicorn backend.main:app --reload
```

## Project Structure

```
├── backend/           # Python backend package
│   ├── models.py     # SQLModel database models
│   ├── database.py   # Database connection management
│   ├── config.py     # Configuration management
│   └── cli.py        # Typer CLI application
├── frontend/         # Frontend package (future)
├── infra/           # Infrastructure configuration
├── migrations/      # Alembic database migrations
├── docs/           # Documentation
│   ├── PRD.md      # Product Requirements Document
│   └── Implementation_Plan.md
└── tests/          # Test suite
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black .
ruff check .
mypy .
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/rag_unito` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | Chat model | `gpt-4o-mini` |
| `API_SECRET_KEY` | JWT secret key | Required |

See `env.example` for complete configuration options.

## Document Classes

The system supports four types of bibliographic documents:

- **authored_by_subject**: Works written by the subject
- **subject_library**: Books the subject read during their life
- **about_subject**: Works written about the subject by others
- **subject_traces**: Fragments and traces left by the subject

## License

[Add your license here]

## Contributing

[Add contributing guidelines here] 