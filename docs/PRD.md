# Product Requirements Document (PRD)

## 1. Purpose  
Build a production-ready prototype that demonstrates how Retrieval-Augmented Generation (RAG) can transform **archival discovery** from keyword look-ups into **narrative, cited conversations**. The prototype must be robust enough for live user studies while remaining lightweight (Postgres + OpenAI only).

### 1.1 Vision & Impact (June 2025)  
• **Lower Access Barriers** – Non-specialists can ask natural-language questions instead of mastering complex catalog syntax.  
• **Reveal Hidden Links** – Cross-document retrieval surfaces relationships (people, places, themes) that are not explicit in metadata.  
• **Storytelling** – The agent can weave sources into coherent explanations, helping curators craft exhibitions or digital narratives.  
• **Research Platform** – Metrics, logs, and user feedback loops will let the team measure whether conversational RAG genuinely outperforms traditional OPAC workflows.

## 2. Stakeholders  
• Project sponsor / domain expert  
• Bibliographic curators (ingestion operators)  
• End-users (researchers, students, public)  
• Dev-Ops & maintenance team  

## 3. System Scope  
### Backend (Python)
1. Document Ingestion & Indexing API/CLI  
2. ReAct-based RAG Conversation API  

### Frontend
• Thin client (web chat) that consumes the Conversation API  
• Optional CLI or simple web panel for ingestion operations  

### Infrastructure
• PostgreSQL ≥ 16 with `pgvector` extension  
• OpenAI API (latest stable) for both embeddings and chat completion  
• Deployable to modern fully managed PaaS (e.g., Fly.io, Render, Railway, AWS AppRunner, GCP Cloud Run)  
• No heavyweight monolithic ML or search frameworks  

## 4. Functional Requirements  
### 4.1 Document Ingestion  
F-1 — Accept an Excel (`.xlsx`) metadata sheet referencing corresponding `.txt` / `.md` content files  
F-2 — Validate and write metadata into Postgres tables  
F-3 — Chunk text or keep whole, based on batch parameters (`chunk_size`, `overlap`, or `no_chunking`)  
F-4 — Compute embeddings with OpenAI and store in `pgvector` column  
F-5 — Expose batch status & statistics through API and/or CLI output  

### 4.2 Conversation (RAG)  
F-6 — Chat endpoint accepts a message history and user prompt  
F-7 — Internal ReAct agent decides whether external retrieval is needed  
F-8 — When retrieval is triggered:  
 • Similarity search on embeddings (top-k, filtered by metadata)  
 • Return chunk text + document-level metadata to the LLM context  
F-9 — LLM produces a grounded answer citing the source documents  
F-10 — Return answer, references, and retrieval trace to client  

### 4.3 Administration  
F-11 — Authentication for ingestion operations (token/bearer)  
F-12 — Health & metrics endpoints (`/healthz`, `/metrics`)  

## 5. Non-Functional Requirements  
• Accuracy: Chat must not hallucinate; every factual span must be sourced  
• Scalability: ≥ 1 k concurrent chat sessions  
• Security: TLS everywhere; secrets in env vars  
• Observability: Structured logs, tracing, and basic Prometheus metrics  
• Portability: Zero state outside Postgres; containerized build  

## 6. Data Model (high-level)  
• `documents`: id, title, author, class, publication_year, …  
• `content_files`: id, document_id, path, checksum  
• `chunks`: id, document_id, batch_id, text, embedding (vector), seq_number  
• `batches`: id, params (jsonb), status, created_at  

## 7. Constraints & Trade-Offs  
• Only OpenAI models → avoids self-hosting GPU costs  
• Postgres chosen over dedicated vector DB to simplify ops  
• Minimal third-party Python libs (FastAPI, SQLAlchemy/SQLModel, Typer, pydantic-settings)  

## 8. Out of Scope  
• Fine-tuning custom LLMs  
• Real-time collaboration features  
• Rich media (images, audio) indexing  