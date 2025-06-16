// Chat message types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

// Citation information
export interface Citation {
  id: string;
  title: string;
  author?: string;
  excerpt: string;
  source_type?: string;
  publication_year?: number;
  document_class?: string;
}

// Backend API types
export interface ChatRequest {
  prompt: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  retrieval_trace?: {
    query_used: string;
    chunks_retrieved: number;
    search_results: any[];
  };
  meta?: {
    mode?: 'chitchat' | 'knowledge';
    token_usage?: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
  };
}

// UI state types
export type ConversationMode = 'chitchat' | 'knowledge' | 'unknown';

export interface ChatState {
  messages: ChatMessage[];
  citations: Map<string, Citation>;
  mode: ConversationMode;
  isLoading: boolean;
  error: string | null;
  sidebarOpen: boolean;
} 