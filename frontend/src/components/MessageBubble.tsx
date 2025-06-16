import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { User, Bot } from 'lucide-react';
import type { ChatMessage, Citation } from '../types';

interface MessageBubbleProps {
  message: ChatMessage;
  citations: Map<string, Citation>;
  onCitationClick: () => void;
}

export default function MessageBubble({ message, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  // Custom component for rendering citations
  const CitationRenderer = ({ children }: { children: React.ReactNode }) => {
    const text = children?.toString() || '';
    const citationRegex = /\[(\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      
      // Add citation link
      const citationNum = match[1];
      parts.push(
        <sup key={`citation-${citationNum}-${match.index}`}>
          <button
            className="citation-link"
            onClick={onCitationClick}
            type="button"
          >
            {citationNum}
          </button>
        </sup>
      );
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    
    return <>{parts}</>;
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`message-bubble ${isUser ? 'message-user' : 'message-assistant'}`}>
        <div className="flex items-start space-x-3">
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-archive-blue-600 text-white' 
              : 'bg-archive-gray-100 text-archive-gray-600'
          }`}>
            {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
          </div>
          
          <div className="flex-1 min-w-0">
            {isUser ? (
              <p className="text-white whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeSanitize]}
                  components={{
                    p: ({ children }) => (
                      <p className="text-archive-gray-900 mb-2 last:mb-0">
                        <CitationRenderer>{children}</CitationRenderer>
                      </p>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-archive-gray-900">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-archive-gray-700">
                        {children}
                      </em>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
            
            {message.timestamp && (
              <div className={`text-xs mt-2 ${
                isUser ? 'text-archive-blue-100' : 'text-archive-gray-400'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 