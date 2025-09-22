# User Guide

This guide covers how to use Biblio RAG's chat interface and manage document ingestion.

## Using the Chat Interface

### Accessing the Application

1. Ensure the application is running (see [Getting Started](getting-started.md))
2. Open your browser to `http://localhost:3000`
3. You'll see a modern chat interface with an input bar at the bottom

### Conversation Modes

Biblio RAG automatically detects and adapts to different conversation types:

**Chitchat Mode** 🗨️
- General greetings and casual conversation
- Examples: "Hello", "Ciao", "How are you?", "Thank you"
- The agent responds as "Archivio", a friendly digital curator
- No knowledge retrieval performed

**Knowledge Mode** 🔍  
- Questions about the ingested document collection
- Examples: "Who was Emanuele Artom?", "What books did Artom read?", "Tell me about Benedetto Croce"
- Agent searches the archive and provides cited responses
- All consulted sources are displayed with full transparency

### Chat Features

**Message Input**
- Type your question in the input bar at the bottom
- Press Enter or click the send button
- Messages support both English and Italian

**Citations and Sources**
- Knowledge responses include inline citations like `[1]`, `[2]`
- Click the menu icon (☰) in the top-right to open the sources sidebar
- The sidebar shows ALL sources the agent consulted, not just those explicitly cited
- Each source includes full bibliographic metadata

**Conversation History**
- Your conversation persists during the session
- Click the trash icon (🗑️) to clear the conversation and start fresh
- Note: Conversations are not saved between browser sessions

**Loading States**
- The interface shows typing indicators while the agent is thinking
- Long responses may take 5-10 seconds for complex knowledge queries

### Example Conversations

**Getting Started**
```
You: Hello
Archivio: Ciao! I'm Archivio, your passionate digital curator for this 
bibliographic collection. I'm here to help you explore the fascinating 
world of Emanuele Artom and the interconnected texts in our archive...
```

**Knowledge Queries** (requires ingested data)
```
You: Who was Emanuele Artom?
Archivio: Emanuele Artom (1915-1944) was a remarkable Italian Jewish 
intellectual, anti-fascist partisan, and diarist [1][2]. Born in Turin 
to a well-educated family, he studied literature and became deeply 
engaged with both classical and contemporary philosophical works...

[Sources sidebar shows: Artom's diary entries, biographical materials, 
historical documents about his life and work]
```

**Follow-up Questions**
```
You: What books did he read?
Archivio: Artom's personal library reflects his deep intellectual 
curiosity, spanning classical literature, philosophy, and contemporary 
works [3][4]. His collection included works by Benedetto Croce, 
classical Greek texts, and modern European literature...
```

**Metadata Queries (New)**
```
You: How many books did Artom write?
Archivio: According to the collection metadata, there are 18 works authored by Emanuele Artom.

You: List the authors in the library.
Archivio: The library contains works by a diverse set of authors, including: Benedetto Croce, Dante Alighieri, Virgil, and many others.
```

## Document Ingestion

### Overview

Biblio RAG requires document ingestion to provide knowledge-based responses. The system processes CSV metadata files that reference text content files, creating searchable embeddings.

### Document Classes

The system supports four types of documents:

- **authored_by_subject**: Works written by the archive subject (e.g., Artom's diary entries)
- **subject_library**: Books from the subject's personal library  
- **about_subject**: Biographical and scholarly works about the subject
- **subject_traces**: Fragments, marginalia, and traces left by the subject

### Ingestion Process

**1. Prepare Your Data**

Your data should consist of:
- **Metadata CSV**: Contains bibliographic information for each document
- **Content Files**: Text files (.txt or .md) with the actual document content

**CSV Structure**: The system auto-detects CSV types based on filename:
- `inventario_*.csv`: Library inventory (subject's personal collection)
- `opera_*.csv`: Works authored by the subject  
- `su_*.csv`: Works about the subject

**Required CSV Columns** (varies by type):
- Title, Author, Year, Publisher, Document Class
- `content_file`: Path to the associated text file

**2. Run Ingestion**

**Basic Ingestion**
```bash
# Ingest the sample Artom collection
uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name "artom-demo"
```

**Advanced Options**
```bash
# Custom chunking parameters
uv run python ingest.py data/my_collection.csv \
  --batch-name "my-collection-v1" \
  --chunk-size 1500 \
  --chunk-overlap 150 \
  --content-path data/texts/

# Disable chunking (embed full documents)
uv run python ingest.py data/my_collection.csv \
  --batch-name "full-docs" \
  --no-chunking
```

**3. Monitor Ingestion Progress**

```bash
# List all ingestion batches
uv run rag-ingest list-batches

# Check specific batch status
uv run rag-ingest status --batch-id <batch-id>

# Sample output:
# Batch: artom-demo (completed)
# Documents: 125 processed, 0 failed
# Chunks: 1,247 embedded
# Duration: 3m 42s
```

### Ingestion Parameters

**Chunk Size** (`--chunk-size`, default: 1000)
- Number of tokens per text chunk
- Larger chunks: More context, fewer chunks
- Smaller chunks: More precise retrieval, more chunks

**Chunk Overlap** (`--chunk-overlap`, default: 100)  
- Token overlap between adjacent chunks
- Prevents information loss at chunk boundaries
- Typically 10-20% of chunk size

**Content Path** (`--content-path`)
- Base directory for content files
- CSV `content_file` column resolved relative to this path

**Batch Name** (`--batch-name`)
- Human-readable identifier for the ingestion batch
- Used for tracking and management

### Sample Data

Biblio RAG includes the **Emanuele Artom** collection for testing:

**Files**:
- `source_data/inventario_Artom_Prandi.csv`: Library inventory metadata (125 entries)
- `source_data/content/`: Text files with document content

**Content Types**:
- Personal diary entries and writings
- Books from Artom's personal library  
- Scholarly works about Artom
- Historical fragments and traces

**To Ingest Sample Data**:
```bash
uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name "artom-collection"
```

After ingestion, you can ask questions like:
- "Who was Emanuele Artom?"
- "What books did Artom read about philosophy?"
- "Tell me about Artom's thoughts on resistance"

### Custom Collections

**Creating Your Own Collection**:

1. **Prepare Metadata CSV**: Follow the column structure of the sample files
2. **Organize Content Files**: Place text files in a directory structure
3. **Update CSV Paths**: Ensure `content_file` column points to correct files
4. **Run Ingestion**: Use the `ingest.py` script with your data

**CSV Requirements**:
- UTF-8 encoding
- Standard CSV format with headers
- `content_file` column with relative paths to text files
- Document classification in appropriate column

## Troubleshooting

### Chat Interface Issues

**No Response to Knowledge Questions**
- Verify documents have been ingested: `uv run rag-ingest list-batches`
- Check that ingestion completed successfully
- Ensure OpenAI API key is configured correctly

**Citations Not Appearing**
- Citations only appear for knowledge-mode responses
- Try more specific questions about ingested content
- Verify the sources sidebar opens with the menu (☰) button

**Slow Response Times**
- Normal for first query (cold start): 5-10 seconds
- Subsequent queries should be faster: 2-5 seconds
- Larger collections may require more processing time

### Ingestion Issues

**CSV Parsing Errors**
```bash
# Check CSV format and encoding
file -I your_file.csv

# Validate with small test batch
head -10 your_file.csv > test.csv
uv run python ingest.py test.csv --batch-name "test"
```

**Content File Not Found**
- Verify `content_file` paths in CSV are correct
- Check that files exist at the specified locations
- Use `--content-path` to set base directory

**OpenAI API Errors**
- Verify API key has sufficient credits
- Check rate limits for your API tier
- Monitor usage in OpenAI dashboard

**Database Connection Issues**
```bash
# Verify database is running
docker ps | grep postgres

# Check database logs
docker-compose -f docker-compose.dev.yml logs postgres

# Reset database if needed
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
uv run rag-ingest init-db
```

### Performance Optimization

**Large Collections**
- Use smaller chunk sizes (500-800 tokens) for precision
- Consider batch processing large datasets
- Monitor embedding API costs and rate limits

**Query Performance**
- More specific questions yield better results
- Include relevant context in queries
- Use proper names and specific terms from your collection