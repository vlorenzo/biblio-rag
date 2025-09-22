// Backend API types
export type Role = 'system' | 'user' | 'assistant';

export interface ChatMessageAPI {
  role: Role;
  content: string;
}

export interface ChatRequest {
  history: ChatMessageAPI[];
  prompt: string;
  session_id?: string | null;
}

export interface Citation {
  id: string;
  title: string;
  author?: string;
  excerpt: string;
  publication_year?: number;
  document_class?: string;
  snippet?: string;
  distance?: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  meta: {
    mode?: string;
    citation_map?: Record<string, Citation>;
  };
  session_id: string;
}

// UI state types
export type ConversationMode = 'chitchat' | 'knowledge' | 'unknown' | 'error';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatState {
  messages: ChatMessage[];
  citations: Map<string, Citation>;
  mode: ConversationMode;
  isLoading: boolean;
  error: string | null;
  sidebarOpen: boolean;
  sessionId: string | null;
} 