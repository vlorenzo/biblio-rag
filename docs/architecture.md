# Architecture

This document provides a comprehensive overview of Biblio RAG's technical architecture and implementation.

## System Overview

Biblio RAG is a three-tier web application designed for conversational access to bibliographic archives. The system combines modern web technologies with intelligent AI agents to provide grounded, cited responses about scholarly collections.

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Frontend      │    │    Backend       │    │     Database       │
│   React + TS    │◄──►│   FastAPI        │◄──►│  PostgreSQL +      │
│   Chat UI       │    │   Smart Engine   │    │  pgvector          │
└─────────────────┘    └──────────────────┘    └────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   OpenAI APIs    │
                       │   Embeddings +   │
                       │   Chat Models    │
                       └──────────────────┘
```

## Core Components

### 1. Smart Engine (`backend/rag/smart_engine.py`)

The **Smart Engine** serves as the central orchestrator, providing a clean interface between the API layer and the AI agent.

**Key Features:**
- Single entry point for chat functionality
- Minimal orchestration logic (delegates decisions to SmartAgent)
- Structured response formatting with citations
- Error handling and logging

**Flow:**
```python
User Query → SmartAgent → Decision (retrieve/respond) → Formatted Response
```

### 2. SmartAgent (`backend/rag/agent/smart_agent.py`)

The **SmartAgent** is the intelligent core of the system, using OpenAI's function calling to make autonomous decisions about when to retrieve knowledge.

**Architecture:**
- **Decision Making**: Uses OpenAI function calling to decide when retrieval is needed
- **Personality**: Operates as "Archivio", a passionate digital curator
- **Tool Integration**: Has access to `retrieve_knowledge` function
- **Conversation Modes**: Handles both chitchat and scholarly discussions

**Agent Configuration:**
- **Model**: GPT-4o-mini for cost-effective, high-quality responses
- **Temperature**: 0.3 for consistent yet natural responses
- **System Prompt**: Detailed persona and behavior instructions
- **Tool Schema**: Single tool for knowledge retrieval with reasoning parameters

**Decision Process:**
1. Receives user query and conversation history
2. Analyzes whether knowledge retrieval is needed
3. If needed, calls `retrieve_knowledge` with search terms
4. Generates response based on retrieved context
5. Returns response with citation metadata

### 3. Database Layer (`backend/models.py`)

**PostgreSQL + pgvector** provides the foundation for both structured data and vector similarity search.

**Core Models:**

**Document Model:**
```python
class Document(BaseModel):
    title: str
    author: Optional[str]
    document_class: DocumentClass  # authored_by_subject, subject_library, etc.
    year: Optional[int]
    publisher: Optional[str]
    # ... bibliographic metadata
```

**Chunk Model:**
```python
class Chunk(BaseModel):
    content: str
    embedding: Vector(1536)  # OpenAI text-embedding-3-small
    document_id: UUID
    token_count: int
    chunk_index: int
```

**Document Classification:**
- `authored_by_subject`: Works written by the archive subject
- `subject_library`: Books from subject's personal collection  
- `about_subject`: Biographical and scholarly works about the subject
- `subject_traces`: Fragments, marginalia, and historical traces

**Vector Search:**
- **Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **Index Type**: HNSW for efficient approximate nearest neighbor search
- **Distance Metric**: Cosine similarity via pgvector's `<->` operator
- **Query Processing**: Automatic embedding generation for user queries

### 4. Retrieval Service (`backend/services/retrieval_service.py`)

**Vector Similarity Search** implementation using pgvector.

**Key Functions:**
- `search_similar_chunks()`: Low-level similarity query returning Chunk objects
- `retrieve_similar_chunks()`: High-level helper that embeds query text and searches

**Search Parameters:**
- **Similarity Threshold**: Default ≤1.0 (configurable)
- **Max Results**: Default 10 chunks per query
- **Document Metadata**: Includes full bibliographic information in results

**Query Process:**
1. Embed user query using OpenAI embedding service
2. Perform cosine similarity search in pgvector
3. Filter by distance threshold
4. Return chunks with associated document metadata

### 5. Frontend Architecture (`frontend/src/`)

**React + TypeScript** single-page application with modern state management.

**Component Hierarchy:**
```
App.tsx
└── ChatPage.tsx
    ├── ChatHeader.tsx (title, controls)
    ├── MessagesPane.tsx (conversation display)
    │   └── MessageBubble.tsx (individual messages)
    ├── ChatInputBar.tsx (user input)
    ├── SourcesSidebar.tsx (citation display)
    └── ErrorBanner.tsx (error handling)
```

**State Management (`hooks/useChat.ts`):**
- **Message History**: Array of user/assistant messages
- **Citations**: Map of citation IDs to source metadata
- **Conversation Mode**: Real-time detection (chitchat/knowledge)
- **Loading States**: Request status and error handling
- **Sidebar Control**: Sources panel visibility

**API Integration (`lib/api.ts`):**
- **REST Client**: Axios-based API communication
- **Error Handling**: Typed error responses with user-friendly messages
- **Request Cancellation**: AbortController for interrupted requests

### 6. Ingestion Pipeline (`backend/services/`)

**Batch Document Processing** for building the knowledge base.

**CSV Parser (`csv_parser.py`):**
- **Auto-Detection**: Identifies CSV type by filename pattern
- **Column Mapping**: Flexible mapping for different metadata schemas
- **Document Classification**: Automatic assignment based on CSV type
- **Error Handling**: Validation and detailed error reporting

**Text Chunker (`text_chunker.py`):**
- **Sliding Window**: Configurable chunk size with overlap
- **Token-Based**: Uses tiktoken for accurate token counting
- **Context Preservation**: Overlap prevents information loss at boundaries
- **Flexible Sizing**: Supports different chunk strategies

**Embedding Service (`embedding_service.py`):**
- **OpenAI Integration**: text-embedding-3-small model
- **Batch Processing**: Efficient embedding generation
- **Error Handling**: Retry logic and rate limit management
- **Cost Optimization**: Deduplication and caching strategies

**Ingestion Workflow:**
```
CSV Metadata → Document Creation → Content File Processing → 
Text Chunking → Embedding Generation → Vector Storage
```

## Data Flow

### 1. Query Processing Flow

```
User Input → Frontend → Backend API → Smart Engine → SmartAgent
                                                        ↓
Citation Extraction ← Response Generation ← OpenAI ← Decision
        ↓
Frontend Display ← Formatted Response ← Smart Engine
```

### 2. Knowledge Retrieval Flow

```
User Query → SmartAgent → retrieve_knowledge() → Embedding Service
                                                        ↓
                                                  Query Embedding
                                                        ↓
Citation Map ← Context Assembly ← Vector Search ← pgvector Database
     ↓
Response Generation (OpenAI) → SmartAgent → Smart Engine
```

### 3. Document Ingestion Flow

```
CSV File → CSV Parser → Document Records → Database Storage
                             ↓
Text Files → Text Chunker → Chunk Records → Embedding Service
                                                    ↓
                                            Vector Embeddings → pgvector Storage
```

## AI Integration

### OpenAI Service Integration

**Models Used:**
- **Chat**: gpt-4o-mini (cost-effective, high-quality responses)
- **Embeddings**: text-embedding-3-small (1536 dimensions)

**Function Calling Schema:**
```json
{
  "name": "retrieve_knowledge",
  "description": "Search the archive for relevant information",
  "parameters": {
    "search_terms": "string",
    "reasoning": "string"
  }
}
```

**Agent System Prompt:**
- **Persona**: "Archivio" - passionate digital curator
- **Behavior**: Scholarly yet approachable communication style
- **Citation Rules**: Must reference all consulted sources
- **Decision Guidelines**: When to retrieve vs. respond directly

### Conversation Intelligence

**Mode Detection:**
- **Chitchat**: Greetings, casual conversation, general questions
- **Knowledge**: Factual queries about the archive content
- **Visual Indicators**: UI adapts based on detected mode

**Response Strategies:**
- **Direct Response**: For conversational queries without retrieval
- **Grounded Response**: For knowledge queries with full citation transparency
- **Error Handling**: Graceful degradation when services unavailable

## Security and Performance

### Security Measures

**API Security:**
- **CORS Configuration**: Restricted origins for frontend access
- **Input Validation**: Pydantic models for request/response validation
- **Error Handling**: Sanitized error messages, no internal details exposed

**Data Security:**
- **Environment Variables**: Sensitive configuration externalized
- **Database Connections**: Parameterized queries prevent injection
- **API Keys**: Secure storage and rotation procedures

### Performance Optimizations

**Database:**
- **HNSW Indexing**: Optimized vector similarity search
- **Connection Pooling**: Async connection management
- **Query Optimization**: Selective loading of document metadata

**Frontend:**
- **Component Optimization**: React.memo for expensive components
- **State Management**: Efficient re-rendering with minimal state updates
- **Asset Optimization**: Vite build optimization and code splitting

**AI Services:**
- **Embedding Caching**: Avoid redundant embedding generation
- **Response Streaming**: Future enhancement for real-time responses
- **Rate Limit Management**: Graceful handling of API limits

## Deployment Architecture

### Development Environment

**Docker Compose Setup:**
- **PostgreSQL**: pgvector/pgvector:pg16 image
- **Application**: Source mounting for hot reload
- **Networking**: Isolated bridge network
- **Volume Management**: Persistent database storage

### Production Deployment

**Multi-Stage Docker Build:**
1. **Frontend Builder**: Node.js → Static assets
2. **Backend Builder**: Python + uv → Virtual environment
3. **Production**: Slim Python base with non-root user

**Fly.io Configuration:**
- **Auto-scaling**: Min 0, auto-start/stop machines
- **Release Command**: Automatic database migrations
- **Resource Allocation**: 1GB RAM, shared CPU
- **Health Checks**: Built-in endpoint monitoring

## Configuration Management

### Environment Variables

**Required Configuration:**
```bash
OPENAI_API_KEY=sk-...          # OpenAI API access
DATABASE_URL=postgresql+...    # Database connection
```

**Optional Configuration:**
```bash
# AI Model Settings
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# RAG Parameters  
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=100
RAG_MAX_CHUNKS=10
RAG_SIMILARITY_THRESHOLD=1.0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### Database Migrations

**Alembic Integration:**
- **Auto-generation**: Schema changes automatically detected
- **Version Control**: Migration history tracked in version control
- **Production Safety**: Review process for schema changes
- **Rollback Support**: Downgrade capabilities for critical issues

## Monitoring and Observability

### Logging

**Structured Logging (loguru):**
- **Trace Logs**: Complete retrieval workflow tracking
- **Performance Metrics**: Query timing and resource usage
- **Error Tracking**: Detailed error context and stack traces
- **Citation Auditing**: Full provenance of consulted sources

### Health Monitoring

**Built-in Endpoints:**
- `/healthz`: Application health status
- `/metrics`: Prometheus-compatible metrics (planned)

**Database Monitoring:**
- Connection pool status
- Query performance metrics
- Vector index health

This architecture provides a robust, scalable foundation for conversational access to bibliographic archives while maintaining academic rigor and source transparency.