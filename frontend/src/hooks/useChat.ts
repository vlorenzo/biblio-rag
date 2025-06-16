import { useState, useCallback, useRef } from 'react';
import type { ChatMessage, ConversationMode, ChatState } from '../types';
import { sendChatMessage, ApiError } from '../lib/api';

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    citations: new Map(),
    mode: 'unknown',
    isLoading: false,
    error: null,
    sidebarOpen: false,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (prompt: string) => {
    if (!prompt.trim() || state.isLoading) return;

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Add user message immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content: prompt.trim(),
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    try {
      abortControllerRef.current = new AbortController();
      
      // Convert frontend messages to backend format (remove timestamp)
      const backendHistory = state.messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await sendChatMessage({
        prompt: prompt.trim(),
        history: backendHistory,
      });

      // Add assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
      };

      // Update citations map
      const newCitations = new Map(state.citations);
      response.citations.forEach(citation => {
        newCitations.set(citation.id, citation);
      });

      // Determine conversation mode
      const mode: ConversationMode = response.meta?.mode || 'unknown';

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        citations: newCitations,
        mode,
        isLoading: false,
        error: null,
      }));

    } catch (error) {
      if (error instanceof ApiError) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message,
        }));
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'An unexpected error occurred',
        }));
      }
    }
  }, [state.messages, state.isLoading]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const toggleSidebar = useCallback(() => {
    setState(prev => ({ ...prev, sidebarOpen: !prev.sidebarOpen }));
  }, []);

  const clearHistory = useCallback(() => {
    setState({
      messages: [],
      citations: new Map(),
      mode: 'unknown',
      isLoading: false,
      error: null,
      sidebarOpen: false,
    });
  }, []);

  return {
    ...state,
    sendMessage,
    clearError,
    toggleSidebar,
    clearHistory,
  };
} 