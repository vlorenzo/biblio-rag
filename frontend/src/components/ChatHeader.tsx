import { BookOpen, Menu, Trash2 } from 'lucide-react';
import type { ConversationMode } from '../types';
import { useI18n } from '../i18n';

interface ChatHeaderProps {
  mode: ConversationMode;
  onToggleSidebar: () => void;
  onClearHistory: () => void;
}

export default function ChatHeader({ mode, onToggleSidebar, onClearHistory }: ChatHeaderProps) {
  const { lang, setLang, t } = useI18n();

  const getModeDisplay = (mode: ConversationMode) => {
    switch (mode) {
      case 'chitchat':
        return { label: t('mode.conversational'), className: 'mode-chitchat' };
      case 'knowledge':
        return { label: t('mode.knowledge'), className: 'mode-knowledge' };
      default:
        return { label: t('mode.ready'), className: 'bg-archive-gray-100 text-archive-gray-600' };
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
                {t('header.title')}
              </h1>
              <p className="text-sm text-archive-gray-500">
                {t('header.subtitle')}
              </p>
            </div>
          </div>
          
          <div className={`mode-badge ${modeDisplay.className}`}>
            {modeDisplay.label}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Simple language toggle (default: Italian). */}
          <div className="flex items-center rounded-md border border-archive-gray-200 bg-white overflow-hidden">
            <button
              type="button"
              onClick={() => setLang('it')}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                lang === 'it'
                  ? 'bg-archive-gray-900 text-white'
                  : 'text-archive-gray-600 hover:bg-archive-gray-100'
              }`}
              aria-pressed={lang === 'it'}
              title="Italiano"
            >
              IT
            </button>
            <button
              type="button"
              onClick={() => setLang('en')}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                lang === 'en'
                  ? 'bg-archive-gray-900 text-white'
                  : 'text-archive-gray-600 hover:bg-archive-gray-100'
              }`}
              aria-pressed={lang === 'en'}
              title="English"
            >
              EN
            </button>
          </div>

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