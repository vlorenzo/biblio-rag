import { useChat } from '../hooks/useChat';
import ChatHeader from '../components/ChatHeader';
import MessagesPane from '../components/MessagesPane';
import ChatInputBar from '../components/ChatInputBar';
import SourcesSidebar from '../components/SourcesSidebar';
import ErrorBanner from '../components/ErrorBanner';

export default function ChatPage() {
  const chat = useChat();

  return (
    <div className="flex h-screen bg-archive-gray-50">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        <ChatHeader 
          mode={chat.mode}
          onToggleSidebar={chat.toggleSidebar}
          onClearHistory={chat.clearHistory}
        />
        
        {chat.error && (
          <ErrorBanner 
            message={chat.error}
            onDismiss={chat.clearError}
          />
        )}
        
        <MessagesPane 
          messages={chat.messages}
          citations={chat.citations}
          isLoading={chat.isLoading}
          onCitationClick={chat.toggleSidebar}
        />
        
        <ChatInputBar 
          onSendMessage={chat.sendMessage}
          isLoading={chat.isLoading}
        />
      </div>

      {/* Sources sidebar */}
      <SourcesSidebar 
        isOpen={chat.sidebarOpen}
        citations={chat.citations}
        onClose={chat.toggleSidebar}
      />
    </div>
  );
} 