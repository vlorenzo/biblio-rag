import React from 'react';
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
    // Helper to process children recursively
    const process = (node: React.ReactNode): React.ReactNode => {
      if (typeof node === 'string') {
        // Only process citation markers in plain text
        const citationRegex = /\[(\d+)\]/g;
        const parts = [];
        let lastIndex = 0;
        let match;
        while ((match = citationRegex.exec(node)) !== null) {
          if (match.index > lastIndex) {
            parts.push(node.slice(lastIndex, match.index));
          }
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
        if (lastIndex < node.length) {
          parts.push(node.slice(lastIndex));
        }
        return parts;
      } else if (Array.isArray(node)) {
        return node.map((child, idx) => <React.Fragment key={idx}>{process(child)}</React.Fragment>);
      } else if (React.isValidElement(node)) {
        // Recursively process children of React elements
        return React.cloneElement(node, node.props, process(node.props.children));
      } else {
        // For null, undefined, boolean, etc.
        return node;
      }
    };
    return <>{process(children)}</>;
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