import { BookOpen, Menu, Trash2 } from 'lucide-react';
import type { ConversationMode } from '../types';

interface ChatHeaderProps {
  mode: ConversationMode;
  onToggleSidebar: () => void;
  onClearHistory: () => void;
}

export default function ChatHeader({ mode, onToggleSidebar, onClearHistory }: ChatHeaderProps) {
  const getModeDisplay = (mode: ConversationMode) => {
    switch (mode) {
      case 'chitchat':
        return { label: 'Conversational', className: 'mode-chitchat' };
      case 'knowledge':
        return { label: 'Knowledge', className: 'mode-knowledge' };
      default:
        return { label: 'Ready', className: 'bg-archive-gray-100 text-archive-gray-600' };
    }
  };

  const modeDisplay = getModeDisplay(mode);

  return (
    <header className="bg-white border-b border-archive-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <BookOpen className="h-8 w-8 text-archive-blue-600" />
            <div>
              <h1 className="text-xl font-serif font-semibold text-archive-gray-900">
                Emanuele Artom Archive
              </h1>
              <p className="text-sm text-archive-gray-500">
                Conversational access to the bibliographic collection
              </p>
            </div>
          </div>
          
          <div className={`mode-badge ${modeDisplay.className}`}>
            {modeDisplay.label}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onClearHistory}
            className="p-2 text-archive-gray-400 hover:text-archive-gray-600 rounded-md hover:bg-archive-gray-100 transition-colors"
            title="Clear conversation history"
          >
            <Trash2 className="h-5 w-5" />
          </button>
          
          <button
            onClick={onToggleSidebar}
            className="p-2 text-archive-gray-400 hover:text-archive-gray-600 rounded-md hover:bg-archive-gray-100 transition-colors"
            title="Toggle sources sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
} 