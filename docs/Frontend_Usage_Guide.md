# Frontend Usage Guide

## Complete System Setup

This guide shows how to run the complete RAG Unito system with both backend API and frontend chat interface.

### Prerequisites

- Python ≥ 3.12
- Node.js ≥ 18
- PostgreSQL ≥ 16 with pgvector extension
- OpenAI API key

### Step 1: Backend Setup

```bash
# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d

# Install Python dependencies
pip install -e ".[dev]"

# Set up environment variables
cp env.example .env
# Edit .env with your OpenAI API key and database settings

# Initialize database
alembic upgrade head

# Ingest sample data (optional)
uv run python ingest.py source_data/inventario_Artom_Prandi.csv --batch-name demo

# Start the backend API
uvicorn backend.api:app --reload
```

The backend will be running at `http://127.0.0.1:8000`

### Step 2: Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the frontend development server
npm run dev
```

The frontend will be running at `http://localhost:3000`

### Step 3: Using the Chat Interface

1. **Open your browser** to `http://localhost:3000`

2. **Start a conversation** by typing in the input field at the bottom

3. **Try different types of queries**:
   - **Greetings**: "Hello", "Hi", "Good morning"
   - **Knowledge questions**: "Who was Emanuele Artom?", "What books did he write?"
   - **Archive queries**: "Tell me about his political activities"

4. **Explore citations**: 
   - Look for numbered citations like `[1]`, `[2]` in responses
   - Click the menu button (☰) to open the sources sidebar
   - View detailed information about each cited source

### Conversation Modes

The system automatically handles two types of conversations:

#### Chitchat Mode 🗣️
- Handles greetings, thanks, and polite conversation
- Provides brief, friendly responses
- Redirects to archive-related topics
- No citations required

#### Knowledge Mode 📚
- Handles factual questions about the archive
- Provides detailed, cited responses
- Shows source documents and excerpts
- Maintains academic rigor

### Interface Features

#### Main Chat Area
- **Message History**: All your conversations are preserved during the session
- **Typing Indicators**: Shows when the system is processing your query
- **Markdown Support**: Responses support formatted text and citations

#### Header
- **Mode Indicator**: Shows current conversation mode (Conversational/Knowledge)
- **Clear History**: Trash icon to start a new conversation
- **Toggle Sidebar**: Menu icon to show/hide sources

#### Sources Sidebar
- **Citation Details**: Full bibliographic information for each source
- **Document Types**: Color-coded icons for different document classes:
  - 📘 **Blue**: Written by Emanuele Artom
  - 📗 **Green**: From Artom's personal library
  - 📙 **Purple**: Written about Artom by others
  - 📕 **Orange**: Traces and fragments left by Artom
- **Excerpts**: Relevant text snippets from each source

#### Input Area
- **Auto-resize**: Text area grows as you type longer messages
- **Keyboard Shortcuts**: 
  - `Enter` to send message
  - `Shift+Enter` for new line
- **Character Counter**: Shows message length (max 2000 characters)

### Troubleshooting

#### Frontend Issues

**"Cannot connect to backend"**
- Ensure backend is running on port 8000
- Check that `VITE_API_BASE` is set correctly
- Verify no firewall blocking the connection

**"Page not loading"**
- Ensure npm dependencies are installed
- Check that port 3000 is available
- Try `npm run build` to check for build errors

#### Backend Issues

**"Database connection failed"**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env file
- Verify pgvector extension is installed

**"OpenAI API errors"**
- Check OPENAI_API_KEY in .env file
- Verify API key has sufficient credits
- Check for rate limiting issues

### Production Deployment

#### Frontend Production Build

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/` and can be:
- Served by the FastAPI backend as static files
- Deployed to static hosting (Netlify, Vercel, Cloudflare Pages)
- Served by any web server (Nginx, Apache)

#### Combined Deployment

To serve frontend from the FastAPI backend:

```python
# In backend/config.py
SERVE_STATIC: bool = True

# In backend/api/__init__.py
if settings.serve_static:
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

### API Endpoints

The frontend uses these backend endpoints:

- `GET /healthz` - Health check
- `POST /chat` - Send chat messages
- `GET /metrics` - Prometheus metrics (optional)

### Environment Variables

#### Backend (.env)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rag_unito
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o-mini
```

#### Frontend (.env.local)
```bash
VITE_API_BASE=http://127.0.0.1:8000
```

### Development Tips

1. **Use browser dev tools** to inspect API calls and debug issues
2. **Monitor backend logs** for detailed error information
3. **Check network tab** for failed API requests
4. **Use React DevTools** for component debugging
5. **Enable hot reload** for faster development

### Next Steps

- **Customize styling** by modifying Tailwind classes
- **Add new features** by extending React components
- **Integrate authentication** for user management
- **Add conversation persistence** with local storage
- **Implement streaming responses** for better UX 