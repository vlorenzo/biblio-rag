# RAG Unito - macOS Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the RAG Unito project on macOS using [uv](https://docs.astral.sh/uv/) as the Python package manager and Docker for PostgreSQL with pgvector.

## Prerequisites

### System Requirements

- **macOS**: 10.15 (Catalina) or later
- **Hardware**: 
  - 8GB RAM minimum (16GB recommended)
  - 20GB free disk space
  - Stable internet connection for OpenAI API

### Required Software

1. **Docker Desktop** (for PostgreSQL + pgvector)
2. **uv** (Python package manager)
3. **Git** (for version control - optional)

## Step 1: Install Docker Desktop

### Download and Install Docker Desktop

1. Visit [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. Download Docker Desktop for Mac (Apple Silicon or Intel)
3. Install Docker Desktop by dragging to Applications folder
4. Launch Docker Desktop from Applications

### Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check if Docker daemon is running
docker info
```

If Docker daemon is not running, start Docker Desktop from Applications.

## Step 2: Install uv (Python Package Manager)

[uv](https://docs.astral.sh/uv/) is an extremely fast Python package and project manager, written in Rust.

### Install uv

```bash
# Install uv using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
uv --version
```

### Alternative Installation Methods

```bash
# Using Homebrew (if you have it)
brew install uv
```

## Step 3: Setup Project

### Get Project Files

**Note**: The project currently exists as local files and is not yet in a git repository.

```bash
# Navigate to your project directory
cd /path/to/RAG_Unito

# Verify project structure exists
ls -la
# Should show: backend/, docs/, tests/, pyproject.toml, docker-compose.dev.yml, etc.
```

### Initialize Python Environment with uv

```bash
# Install Python 3.12 (uv will manage this)
uv python install 3.12

# Create virtual environment and install dependencies
uv sync

# Verify installation
uv run rag-ingest --help
```

**Expected output:**
```
Usage: rag-ingest [OPTIONS] COMMAND [ARGS]...

RAG Unito document ingestion and management CLI

Commands:
  ingest         Ingest documents from CSV metadata file.
  status         Check ingestion batch status.
  list-batches   List all ingestion batches.
  init-db        Initialize database tables.
```

## Step 4: Start PostgreSQL with Docker

### Start PostgreSQL Container

```bash
# Start Docker Desktop if not running
open -a Docker

# Wait for Docker to start, then start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres
```

**Expected output:**
```
[+] Running 3/3
 ✔ Network rag_unito_default         Created
 ✔ Volume "rag_unito_postgres_data"  Created
 ✔ Container rag_unito-postgres-1    Started
```

### Verify PostgreSQL is Running

```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps
```

**Expected output:**
```
NAME                   IMAGE                    COMMAND                  SERVICE    CREATED          STATUS                   PORTS
rag_unito-postgres-1   pgvector/pgvector:pg16   "docker-entrypoint.s…"   postgres   12 seconds ago   Up 11 seconds (healthy)   0.0.0.0:5432->5432/tcp
```

### Test PostgreSQL Connection

```bash
# Test basic connection
docker exec rag_unito-postgres-1 psql -U postgres -d rag_unito -c "SELECT version();"
```

**Expected output:**
```
PostgreSQL 16.4 (Debian 16.4-1.pgdg120+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
```

### Verify pgvector Extension

```bash
# Check pgvector extension
docker exec rag_unito-postgres-1 psql -U postgres -d rag_unito -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

**Expected output:**
```
NOTICE:  extension "vector" already exists, skipping
CREATE EXTENSION
 extname 
---------
 vector
```

### Test Vector Operations

```bash
# Test vector distance calculation
docker exec rag_unito-postgres-1 psql -U postgres -d rag_unito -c "SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector AS distance;"
```

**Expected output:**
```
     distance      
-------------------
 5.196152422706632
```

## Step 5: Environment Configuration

### Create Environment File

```bash
# Copy example environment file
cp env.example .env

# Edit environment file with your preferred editor
nano .env
```

### Configure Environment Variables

Edit `.env` file with your specific settings:

```bash
# Database Configuration (Docker setup)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/rag_unito

# OpenAI Configuration (REQUIRED - get from OpenAI Platform)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini

# API Configuration (has defaults, can be left as-is for development)
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=dev-secret-key-change-in-production

# Ingestion Configuration (has defaults)
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=100
MAX_CONCURRENT_EMBEDDINGS=10

# RAG Configuration (has defaults)
MAX_RETRIEVAL_RESULTS=5
SIMILARITY_THRESHOLD=0.7

# Logging Configuration (has defaults)
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

**Note**: The application will work for basic testing without an OpenAI API key, but embedding operations will fail.

## Step 6: Test the Installation

### Test CLI Commands (Status / Init Only)

```bash
# Main CLI help (still useful for status and init)
uv run rag-ingest --help

# Initialise database tables
uv run rag-ingest init-db   # Alembic upgrade runs

# List batches / check status
uv run rag-ingest list-batches
uv run rag-ingest status
```

> **Note**  
> Il vecchio comando `rag-ingest ingest` è stato dismesso: l\'ingestion vera e propria è ora gestita dallo script `ingest.py` (vedere Step&nbsp;7).

## Step 7: Eseguire l\'ingestion con `ingest.py`

Lo script "stand-alone" mantiene un singolo event-loop e ha dimostrato di risolvere definitivamente l\'errore *greenlet_spawn*.

```bash
# Ingerisci il CSV (senza chunking, batch name personalizzato)
uv run python ingest.py source_data/inventario_Artom_Prandi.csv \
    --no-chunking --batch-name primo_batch
```

Opzioni disponibili:

```
--chunk-size INT        Dimensione dei chunk (default 1000)
--chunk-overlap INT     Overlap tra chunk (default 100)
--no-chunking           Disabilita il chunking (embed documento intero)
--batch-name TEXT       Nome del batch (di default auto-generato)
--content-path TEXT     Base path per i file di contenuto
```

**Output atteso (senza file di testo):**
```
INFO  … Data preparation complete. Found 409 documents.
INFO  … Updated batch … status to processing
INFO  … Updated batch … status to completed
✅ Ingestion completed successfully!
Batch ID: …
Documents processed: 409/409
Total chunks: 0
```

## Che cosa funziona adesso

* Docker + Postgres + pgvector (Step 4)  
* Ambiente Python gestito da uv (Step 2)  
* CLI Typer per `init-db`, `status`, `list-batches`  
* Script `ingest.py` per l\'ingestion batch (Step 7)

Le parti restanti della guida restano valide; dove veniva citato `rag-ingest ingest` sostituiscilo con lo script `ingest.py`.

## Step 8: Frontend Chat Interface Setup (NEW)

### ✅ **Complete Web Application**

The system now includes a full React + TypeScript frontend that provides a modern chat interface for the Emanuele Artom archive.

### Install Node.js and Frontend Dependencies

**Prerequisites:**
- Node.js ≥ 18 (check with `node --version`)
- npm (comes with Node.js)

**Install Node.js (if not present):**
```bash
# Using Homebrew (recommended)
brew install node

# Or download from https://nodejs.org/
```

**Install Frontend Dependencies:**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify installation
npm run build
```

**Expected output:**
```
✓ 1626 modules transformed.
dist/index.html                   0.97 kB │ gzip:   0.53 kB
dist/assets/index-UkZg6WcM.css   34.23 kB │ gzip:   5.64 kB
dist/assets/index-D9-984NK.js   322.04 kB │ gzip: 100.05 kB │ map: 1,386.03 kB
✓ built in 988ms
```

## Step 9: Test the Complete Application

### ✅ **End-to-End Testing**

Test the complete frontend + backend system.

### Start Both Backend and Frontend

**Terminal 1 - Start Backend API:**
```bash
# Make sure you're in the project root directory
uvicorn backend.api:app --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/Users/lorenzov/_SW_Projects/RAG_Unito']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Terminal 2 - Start Frontend Development Server:**
```bash
# Navigate to frontend directory
cd frontend

# Start the development server
npm run dev
```

**Expected output:**
```
  VITE v5.4.19  ready in 75 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Test the Complete Web Application

**1. Open the Chat Interface:**
- Open your browser and navigate to: **http://localhost:3000**
- You should see the "Emanuele Artom Archive" chat interface

**2. Test Conversation Modes:**

**Chitchat Mode:**
```
Type: "Hello"
Expected: "Hi! How can I help you with the Emanuele Artom collection?"
```

**Knowledge Mode (Empty Archive):**
```
Type: "Who was Emanuele Artom?"
Expected: "I couldn't find any information about that in the Emanuele Artom archive yet."
```

**3. Verify Interface Features:**
- ✅ **Message Input**: Text area auto-resizes as you type
- ✅ **Send Button**: Click or press Enter to send messages
- ✅ **Mode Indicator**: Header shows conversation mode (Conversational/Knowledge)
- ✅ **Sources Sidebar**: Click menu (☰) to toggle sources panel
- ✅ **Error Handling**: Network errors display dismissible error banners
- ✅ **Responsive Design**: Try resizing browser window

**4. Test API Health (Optional):**
```bash
# Test backend health directly
curl http://127.0.0.1:8000/healthz
# Expected: {"status":"ok"}
```

### Interactive API Documentation

Open your browser to: **http://127.0.0.1:8000/docs**

This provides FastAPI's automatic interactive documentation where you can:
- View all available endpoints
- Test the `/chat` endpoint with different inputs
- See request/response schemas
- Try different conversation histories

### What the Complete Application Does Right Now

**Frontend Features:**
- ✅ **Modern Chat Interface**: Professional, responsive web application
- ✅ **Real-time Messaging**: Instant communication with backend API
- ✅ **Conversation Intelligence**: Automatic detection of chitchat vs knowledge queries
- ✅ **Citation System**: Inline numbered citations with expandable sources sidebar
- ✅ **Error Recovery**: Graceful handling of network issues and API errors
- ✅ **Academic Design**: Appropriate styling for scholarly content

**Backend Capabilities:**
- ✅ **Complete RAG Pipeline**: Retrieval → prompt building → ReAct agent → guardrails
- ✅ **Database Integration**: Vector similarity search with PostgreSQL + pgvector
- ✅ **API Endpoints**: Health checks, metrics, and chat functionality
- ✅ **CORS Support**: Proper cross-origin resource sharing for web clients
- ✅ **Enhanced UX**: Improved error messages that distinguish "no data" vs "out of scope"

**Note:** Without ingested documents, the system returns helpful messages like "I couldn't find any information about that in the Emanuele Artom archive yet." Once you ingest content with embeddings, the chat will provide grounded answers with source citations.

## Step 9: Test Document Ingestion (Experimental)

### ⚠️ **Current Status**

**Important**: Full document ingestion is implemented but **not fully tested**. This requires:
- Working database initialization
- Valid OpenAI API key
- Proper CSV files in `source_data/` directory

### Attempt Document Ingestion

```bash
# Try to ingest documents (experimental)
uv run rag-ingest ingest source_data/inventario_Artom_Prandi.csv \
    --chunk-size 1000 \
    --chunk-overlap 100 \
    --batch-name "test_inventario"
```

**This may work or may fail** depending on:
- Database initialization success
- OpenAI API key configuration
- CSV file availability

### Check Ingestion Status

```bash
# List all batches
uv run rag-ingest list-batches

# Check specific batch status
uv run rag-ingest status
```

## What Actually Works Right Now

### ✅ **Confirmed Working**

1. **Complete Web Application**: Full React + TypeScript frontend at `http://localhost:3000`
2. **End-to-End Communication**: Frontend ↔ Backend API ↔ Database pipeline
3. **Conversation Intelligence**: Chitchat vs knowledge mode detection with proper responses
4. **Professional UI**: Modern chat interface with citations, error handling, responsive design
5. **Docker Setup**: PostgreSQL + pgvector container starts and works
6. **Python Environment**: uv sync creates working virtual environment
7. **CLI Commands**: All CLI help commands work
8. **CSV Parsing**: Text parsing and chunking works (test_ingestion.py)
9. **Database Connection**: PostgreSQL container accepts connections
10. **Vector Operations**: pgvector extension works for similarity calculations
11. **CORS Integration**: Frontend and backend communicate properly

### ❓ **Experimental/Untested**

1. **Database Initialization**: `init-db` command exists but not fully tested
2. **Full Ingestion Pipeline**: End-to-end document ingestion not verified with actual content files
3. **Batch Management**: Status and listing commands exist but not tested with real ingestion data

### ❌ **Known Missing**

1. **Production Deployment**: No deployment configuration
2. **Document Content**: Archive needs text files for meaningful knowledge responses
3. **Comprehensive Testing**: Many components lack thorough testing

## Troubleshooting

### Docker Issues

```bash
# If Docker daemon not running
open -a Docker

# Check Docker status
docker info

# Restart PostgreSQL container
docker-compose -f docker-compose.dev.yml restart postgres

# View container logs
docker-compose -f docker-compose.dev.yml logs postgres
```

### Python/uv Issues

```bash
# Recreate virtual environment
rm -rf .venv
uv sync

# Check Python version
uv run python --version

# Verify package installation
uv run python -c "import backend; print('Backend module loaded')"
```

### Database Connection Issues

```bash
# Test database connection
docker exec rag_unito-postgres-1 psql -U postgres -d rag_unito -c "SELECT 1;"

# Check container health
docker-compose -f docker-compose.dev.yml ps
```

## Managing the Development Environment

### Starting/Stopping Services

```bash
# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# Stop PostgreSQL
docker-compose -f docker-compose.dev.yml down

# Stop and remove all data
docker-compose -f docker-compose.dev.yml down -v
```

### Development Workflow

```bash
# Daily startup
docker-compose -f docker-compose.dev.yml up -d postgres
source .venv/bin/activate  # or just use 'uv run' prefix

# Run tests
uv run python test_ingestion.py

# Try CLI commands
uv run rag-ingest --help

# Daily shutdown
docker-compose -f docker-compose.dev.yml down
```

## Next Steps

After successful setup, you can:

1. **Test Database Initialization**: Try `uv run rag-ingest init-db`
2. **Configure OpenAI API**: Add your API key to `.env`
3. **Test Full Ingestion**: Try ingesting a small CSV file
4. **Develop Missing Features**: Implement and test remaining functionality
5. **Create Git Repository**: Initialize version control when ready

## Useful Commands Reference

```bash
# Complete Application Startup
uvicorn backend.api:app --reload         # Terminal 1: Start backend API
cd frontend && npm run dev                # Terminal 2: Start frontend

# Docker management
docker-compose -f docker-compose.dev.yml up -d postgres    # Start PostgreSQL
docker-compose -f docker-compose.dev.yml down              # Stop services
docker-compose -f docker-compose.dev.yml ps                # Check status
docker-compose -f docker-compose.dev.yml logs postgres     # View logs

# Frontend development
cd frontend                               # Navigate to frontend
npm install                               # Install dependencies
npm run dev                              # Start development server (port 3000)
npm run build                            # Build for production
npm run preview                          # Preview production build

# Python environment
uv sync                                    # Install/update dependencies
uv run command                            # Run command in virtual environment
uv run python --version                  # Check Python version

# CLI commands (experimental)
uv run rag-ingest --help                 # Main help
uv run rag-ingest init-db                # Initialize database
uv run rag-ingest list-batches           # List batches
uv run rag-ingest status                 # Check status

# Standalone ingestion (recommended)
uv run python ingest.py file.csv --no-chunking --batch-name demo  # Ingest documents

# Database access
docker exec rag_unito-postgres-1 psql -U postgres -d rag_unito    # Connect to database

# Testing
uv run python test_ingestion.py          # Test CSV parsing (works)
uv run pytest                            # Run unit tests (experimental)

# API testing (direct)
curl http://127.0.0.1:8000/healthz       # Test health endpoint
curl http://127.0.0.1:8000/metrics       # Test metrics endpoint
curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"prompt":"test","history":[]}' # Test chat

# Application URLs
# Frontend: http://localhost:3000         # Main chat interface
# Backend API: http://127.0.0.1:8000     # API endpoints
# API Docs: http://127.0.0.1:8000/docs   # Interactive documentation
```

This guide reflects the **actual current state** of the implementation as of the most recent testing. 