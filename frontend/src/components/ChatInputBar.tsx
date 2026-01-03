import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { useI18n } from '../i18n';

interface ChatInputBarProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInputBar({ onSendMessage, isLoading }: ChatInputBarProps) {
  const { t } = useI18n();
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <div className="border-t border-archive-gray-200 bg-white px-6 py-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('input.placeholder')}
              className="w-full px-4 py-3 border border-archive-gray-300 rounded-lg focus:ring-2 focus:ring-archive-blue-500 focus:border-transparent resize-none min-h-[52px] max-h-32"
              disabled={isLoading}
              rows={1}
            />
          </div>
          
          <button
            type="submit"
            disabled={!message.trim() || isLoading}
            className="flex-shrink-0 bg-archive-blue-600 hover:bg-archive-blue-700 disabled:bg-archive-gray-300 disabled:cursor-not-allowed text-white p-3 rounded-lg transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        
        <div className="flex justify-between items-center mt-2 text-xs text-archive-gray-500">
          <span>{t('input.hint')}</span>
          <span>{message.length}/2000</span>
        </div>
        <div className="mt-1 text-[11px] text-archive-gray-400 text-center">
          {t('footer.beta')}
        </div>
      </form>
    </div>
  );
} 