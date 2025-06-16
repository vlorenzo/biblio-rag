# RAG Unito Frontend

Beautiful chat interface for the Emanuele Artom bibliographic archive conversational agent.

## Features

- 🎨 **Modern UI**: Clean, academic-focused design with Tailwind CSS
- 💬 **Smart Conversations**: Handles both chitchat and knowledge queries seamlessly  
- 📚 **Citation Display**: Inline citations with detailed source sidebar
- 📱 **Responsive**: Works on desktop, tablet, and mobile devices
- ⚡ **Real-time**: Instant responses with loading states and error handling
- 🔍 **Document Types**: Visual indicators for different document classes in the archive

## Tech Stack

- **React 18** with TypeScript for type-safe component development
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for utility-first styling with academic color palette
- **React Markdown** with sanitization for safe content rendering
- **Lucide React** for consistent, beautiful icons

## Quick Start

### Prerequisites

- Node.js ≥ 18
- npm or yarn
- Backend API running on port 8000 (or configure `VITE_API_BASE`)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Configuration

Create a `.env.local` file:

```env
# Backend API base URL (default: http://127.0.0.1:8000)
VITE_API_BASE=http://127.0.0.1:8000
```

### Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

## Architecture

### Component Structure

```
src/
├── components/          # Reusable UI components
│   ├── ChatHeader.tsx   # Header with title and mode indicator
│   ├── MessagesPane.tsx # Chat messages container
│   ├── MessageBubble.tsx# Individual message rendering
│   ├── ChatInputBar.tsx # Message input with auto-resize
│   ├── SourcesSidebar.tsx# Citations and sources panel
│   └── ErrorBanner.tsx  # Error display component
├── hooks/
│   └── useChat.ts       # Chat state management and API calls
├── lib/
│   └── api.ts           # Backend API client
├── pages/
│   └── ChatPage.tsx     # Main chat interface page
├── types.ts             # TypeScript type definitions
└── App.tsx              # Root application component
```

### Key Features

**Conversation Modes**
- **Chitchat Mode**: Handles greetings, thanks, and casual conversation
- **Knowledge Mode**: Provides cited, factual responses about the archive
- **Automatic Detection**: Backend determines appropriate mode per query

**Citation System**
- Inline citation links `[1]`, `[2]` in responses
- Detailed source information in collapsible sidebar
- Document type indicators (authored by subject, subject's library, about subject, traces)

**Responsive Design**
- Mobile-first approach with Tailwind CSS
- Collapsible sidebar on smaller screens
- Touch-friendly interface elements

## API Integration

The frontend communicates with the FastAPI backend via:

- `POST /chat` - Send messages and receive responses
- `GET /healthz` - Check backend health status

### Response Format

```typescript
interface ChatResponse {
  answer: string;
  citations: Citation[];
  meta?: {
    mode?: 'chitchat' | 'knowledge';
    token_usage?: TokenUsage;
  };
}
```

## Customization

### Styling

The app uses a custom Tailwind configuration with academic-focused colors:

- `archive-blue`: Primary blue palette for interactive elements
- `archive-gray`: Neutral grays for text and backgrounds
- `font-serif`: Crimson Text for headings (academic feel)
- `font-sans`: Inter for body content (readability)

### Document Types

The sidebar displays different icons and colors for document classes:

- **authored_by_subject**: Works written by Emanuele Artom (blue)
- **subject_library**: Books from Artom's personal library (green)  
- **about_subject**: Works written about Artom by others (purple)
- **subject_traces**: Fragments and traces left by Artom (orange)

## Development

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Create production build
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint for code quality

### Code Quality

The project includes:

- TypeScript for type safety
- ESLint for code quality
- Prettier integration (via editor)
- Component-based architecture
- Accessibility considerations

## Deployment

### Static Hosting

The built frontend is a static SPA that can be deployed to:

- Netlify
- Vercel  
- Cloudflare Pages
- GitHub Pages
- Any static hosting service

### FastAPI Integration

For single-domain deployment, the FastAPI backend can serve the built frontend:

```python
# In backend/api/__init__.py
from fastapi.staticfiles import StaticFiles

if settings.serve_static:
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

## Contributing

1. Follow the existing component structure
2. Use TypeScript for all new components
3. Maintain responsive design principles
4. Test across different screen sizes
5. Ensure accessibility compliance

## License

This project is part of the RAG Unito academic archive system. 