# RAG Unito

A research application for evaluating Large Language Model and Retrieval-Augmented Generation (RAG) technologies in library science. Provides conversational access to bibliographic archives to study how AI can enhance user experience with scholarly collections.

### Vision

Libraries and archives hold vast, inter-connected texts that are hard to browse or synthesize. By fusing structured metadata, full-text search, and a Retrieval-Augmented Language Model, this project lets users ask **"higher-order" questions** ("How did the subject's thinking evolve over time?") and receive grounded answers that cite the primary sources.

The codebase is a **research testbed (June 2025)** for evaluating whether such conversational access can:
• Increase discovery of under-used items  
• Enable narrative storytelling across disparate documents  
• Lower the barrier for non-experts to engage with scholarly collections

**Research Questions**  
1. Does conversational retrieval improve recall/precision vs. traditional OPAC search?  
2. Can grounded LLM answers help users build mental models of a collection faster?  
3. What UI cues prevent hallucinations and maintain trust?

**Current Dataset**: Emanuele Artom bibliographic archive (sample collection for testing and evaluation)

## Features

- **Complete Web Interface**: Modern React + TypeScript chat application
- **Conversation Intelligence**: Automatic detection of chitchat vs knowledge queries
- **Citation System**: Inline citations and a sidebar showing all consulted sources for full transparency.
- **Document Classification**: Support for authored works, library items, biographical materials, and traces
- **Vector Search**: PostgreSQL with pgvector for semantic similarity search
- **ReAct Agent**: Intelligent reasoning using OpenAI function calling
- **Academic Rigor**: Proper bibliographic metadata handling and source attribution

## Quick Start

### Prerequisites

- Python ≥ 3.12
- Node.js ≥ 18
- Docker (for PostgreSQL + pgvector)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vlorenzo/biblio-rag.git
cd biblio-rag
```

2. Install Python dependencies with uv:
```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

3. Start PostgreSQL with Docker:
```bash
docker-compose -f docker-compose.dev.yml up -d postgres
```

4. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your OpenAI API key
```

5. Initialize the database:
```bash
uv run rag-ingest init-db
```

### Usage

#### Running the Application

1. **Start the backend API** (in one terminal):
```bash
uvicorn backend.api:app --reload
```

2. **Start the frontend** (in another terminal):
```bash
cd frontend
npm install  # first time only
npm run dev
```

3. **Open your browser** to `http://localhost:3000`

#### Using the Chat Interface

- **Greetings**: Try "Hello" or "Ciao" for friendly chitchat.
- **Knowledge Questions**: Once you have ingested documents (see below), ask questions like "Who was Emanuele Artom?" or "Did Artom read Benedetto Croce?" to get grounded, cited answers.
- **Sources**: Click the menu (☰) to view the sources the agent consulted for its answer. The UI shows all consulted sources for full transparency, even if not explicitly cited in the text.

### Ingesting Documents (Recommended)

To unlock the full RAG capabilities of the application, you must ingest the provided sample dataset.

1. **Run the Ingestion Script**

   The simplest way is to use the standalone `ingest.py` script. This will process the metadata, chunk the content, and generate the necessary embeddings.

   ```bash
   uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name "artom-collection-v1"
   ```

2. **Verify Ingestion Status**

   You can check the status of your ingestion batches using the `rag-ingest` CLI tool.

   ```bash
   # List all ingestion batches
   uv run rag-ingest list-batches

   # Get detailed status for a specific batch
   uv run rag-ingest status --batch-id <your-batch-id>
   ```

Now that the database is populated, the chat interface will be able to answer knowledge-based questions.

## Project Structure

```
├── backend/           # Python backend package
│   ├── api/          # FastAPI application and routes
│   ├── rag/          # RAG engine and conversation logic
│   ├── services/     # Business logic services
│   ├── models.py     # SQLModel database models
│   ├── database.py   # Database connection management
│   ├── config.py     # Configuration management
│   └── cli.py        # Typer CLI application
├── frontend/         # React + TypeScript frontend
│   ├── src/          # Frontend source code
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom React hooks
│   │   ├── lib/         # Utility libraries
│   │   └── pages/       # Page components
│   ├── package.json  # Node.js dependencies
│   └── README.md     # Frontend documentation
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
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install

# Start development services
docker-compose -f docker-compose.dev.yml up -d postgres
```

### Development Workflow

```bash
# Backend development
uvicorn backend.api:app --reload

# Frontend development (in another terminal)
cd frontend && npm run dev

# Run basic tests
uv run python test_ingestion.py
```

### Database Management

**For Users - Quick Setup:**
```bash
# Initialize database with current schema
uv run rag-ingest init-db
```

**For Developers - Schema Changes:**
```bash
# Create new migration after modifying models
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration if needed
alembic downgrade -1

# Database access
docker exec -it rag_unito-postgres-1 psql -U postgres -d rag_unito
```

## Configuration

Key environment variables (create `.env` file from `env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | **Required** |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:postgres@localhost:5433/rag_unito` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | Chat model | `gpt-4o-mini` |

The application uses sensible defaults for most settings. See `env.example` for complete configuration options.

## Document Classes

The system supports configurable document classification. Current example types (from Emanuele Artom dataset):

- **authored_by_subject**: Works written by the subject
- **subject_library**: Books from the subject's personal library
- **about_subject**: Works written about the subject by others
- **subject_traces**: Fragments and traces left by the subject

*Note: Document classes are configurable and can be adapted for different archives and collections.*

## Current Status

**✅ What Works:**
- Complete web chat interface with modern UI
- Conversation intelligence (chitchat vs knowledge modes)
- Backend API with vector search capabilities and full evidence transparency
- OpenAI integration for embeddings and responses
- PostgreSQL + pgvector database setup
- CSV metadata parsing and ingestion pipeline

**⚠️ Current Limitations:**
- The application requires document ingestion to provide knowledge-based answers. A sample dataset is provided in `source_data/`.
- Production deployment configuration not yet set up

**🎯 Try It:**
To experience the full power of the application, ingest the sample dataset using the instructions above. This will enable the agent to provide cited, scholarly responses to your questions about the Emanuele Artom collection.

**📚 Research Purpose:**
This system serves as a testbed for evaluating how conversational AI can improve access to library and archival collections, with applications in digital humanities, library science, and information retrieval research.

## Architecture

- **Frontend**: React + TypeScript with Tailwind CSS
- **Backend**: FastAPI with async support
- **Database**: PostgreSQL 16 with pgvector for vector similarity search
- **AI**: OpenAI APIs for embeddings and chat completions
- **Agent**: ReAct pattern for intelligent reasoning and tool use