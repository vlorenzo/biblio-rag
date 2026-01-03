import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import MessageBubble from './MessageBubble';
import type { ChatMessage, Citation } from '../types';
import { useI18n } from '../i18n';

interface MessagesPaneProps {
  messages: ChatMessage[];
  citations: Map<string, Citation>;
  isLoading: boolean;
  onCitationClick: () => void;
}

export default function MessagesPane({ 
  messages, 
  citations, 
  isLoading, 
  onCitationClick 
}: MessagesPaneProps) {
  const { t } = useI18n();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <div className="text-archive-gray-400 mb-4">
              <svg 
                className="mx-auto h-12 w-12" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={1.5} 
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" 
                />
              </svg>
            </div>
            <h3 className="text-lg font-serif font-medium text-archive-gray-900 mb-2">
              {t('welcome.heading')}
            </h3>
            <p className="text-archive-gray-500 max-w-md mx-auto">
              {t('welcome.body')}
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            citations={citations}
            onCitationClick={onCitationClick}
          />
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="message-bubble message-assistant">
              <div className="flex items-center space-x-2 text-archive-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{t('loading.searching')}</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
} 