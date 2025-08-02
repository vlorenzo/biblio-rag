# Getting Started

This guide covers detailed installation and deployment options for RAG Unito.

## Prerequisites

### System Requirements
- **Python**: 3.12 or higher
- **Node.js**: 18 or higher  
- **Docker**: For PostgreSQL with pgvector extension
- **OpenAI API Key**: Required for embeddings and chat completion

### Development Tools
- **uv**: Python package manager (installed automatically)
- **PostgreSQL**: 16+ with pgvector extension (via Docker)

## Installation Methods

### Option 1: Local Development (Recommended)

**1. Clone and Setup Dependencies**
```bash
git clone https://github.com/vlorenzo/rag-unito.git
cd rag-unito

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..
```

**2. Database Setup**
```bash
# Start PostgreSQL with pgvector
docker-compose -f docker-compose.dev.yml up -d postgres

# Wait for database to be ready, then initialize
uv run rag-ingest init-db
```

**3. Environment Configuration**
```bash
# Copy example environment file
cp env.example .env

# Edit .env file with your OpenAI API key
# Required: OPENAI_API_KEY=your_api_key_here
```

**4. Data Ingestion (Essential)**
```bash
# Ingest sample Artom collection
uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name "artom-demo"

# Verify ingestion status
uv run rag-ingest list-batches
```

**5. Start Application**
```bash
# Terminal 1: Backend API
uvicorn backend.api:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

**6. Access Application**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### Option 2: Docker Deployment

**Full Application Stack**
```bash
# Clone repository
git clone https://github.com/vlorenzo/rag-unito.git
cd rag-unito

# Create environment file
cp env.example .env
# Edit .env with your OpenAI API key

# Build and start entire stack
docker-compose up --build

# In another terminal, initialize database
docker-compose exec app uv run rag-ingest init-db

# Ingest sample data
docker-compose exec app uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name "artom-demo"
```

**Access**: Application available at `http://localhost:8000`

### Option 3: Production Deployment (Fly.io)

**Prerequisites**: Fly CLI installed and authenticated

```bash
# Deploy to Fly.io
fly deploy

# Set environment variables
fly secrets set OPENAI_API_KEY=your_api_key_here

# Database initialization runs automatically via release_command
```

The `fly.toml` configuration includes:
- Automatic database migrations on deployment
- 1GB RAM, shared CPU
- Auto-start/stop machines
- Amsterdam region (configurable)

## Environment Configuration

### Required Variables

Create `.env` file from `env.example`:

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_api_key_here

# Database (uses Docker default if not specified)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/rag_unito

# AI Models (defaults provided)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
```

### Optional Configuration

```bash
# RAG Parameters
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=100
RAG_MAX_CHUNKS=10
RAG_SIMILARITY_THRESHOLD=1.0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Database Management

### Development Database

```bash
# Start/stop database
docker-compose -f docker-compose.dev.yml up -d postgres
docker-compose -f docker-compose.dev.yml down

# Access database directly
docker exec -it rag_unito-postgres-1 psql -U postgres -d rag_unito

# Reset database (WARNING: destroys all data)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
uv run rag-ingest init-db
```

### Schema Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View database logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart database
docker-compose -f docker-compose.dev.yml restart postgres
```

**OpenAI API Errors**
- Verify API key is set correctly in `.env`
- Check API key has sufficient credits
- Ensure models are available (gpt-4o-mini, text-embedding-3-small)

**Frontend Build Issues**
```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Port Conflicts**
- Backend (8000): Change in `uvicorn` command or set `API_PORT` in `.env`
- Frontend (3000): Vite will auto-increment to 3001, 3002, etc.
- Database (5433): Change in `docker-compose.dev.yml`

### Verification Steps

**Test Database Connection**
```bash
uv run python -c "
from backend.database import get_database
import asyncio
async def test():
    db = get_database()
    print('Database connection successful')
asyncio.run(test())
"
```

**Test OpenAI Integration**
```bash
uv run python -c "
from backend.services.embedding_service import EmbeddingService
import asyncio
async def test():
    service = EmbeddingService()
    result = await service.embed_text('test')
    print(f'Embedding generated: {len(result)} dimensions')
asyncio.run(test())
"
```

**Test API Endpoints**
```bash
# Health check
curl http://localhost:8000/healthz

# Chat endpoint (requires ingested data)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "history": []}'
```

## Development Workflow

**Daily Development**
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d postgres
uvicorn backend.api:app --reload &
cd frontend && npm run dev

# Run tests
uv run pytest

# Check code quality
uv run ruff check
uv run mypy backend/
```

**Working with Data**
```bash
# List ingestion batches
uv run rag-ingest list-batches

# Check batch status
uv run rag-ingest status --batch-id <batch-id>

# Ingest new CSV
uv run python ingest.py path/to/metadata.csv --batch-name "my-collection"
```