/**
 * Backend API client for chat functionality.
 */

import type { ChatRequest, ChatResponse } from '../types';

function normalizeBaseUrl(raw?: string) {
  const base = (raw ?? '').trim().replace(/\/+$/, '');
  // If unset, use same-origin (works on Fly where frontend is served by FastAPI).
  if (!base) return '';
  // Safety: a production build should never point to localhost.
  if (import.meta.env.PROD && /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?$/i.test(base)) {
    return '';
  }
  return base;
}

const API_BASE = normalizeBaseUrl(import.meta.env.VITE_API_BASE);

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Send a chat message to the backend API.
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const url = `${API_BASE}/chat`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(
        `API request failed: ${errorText || response.statusText}`,
        response.status
      );
    }

    const data = await response.json();
    return data as ChatResponse;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Check backend health status.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/healthz`);
    return response.ok;
  } catch {
    return false;
  }
}
