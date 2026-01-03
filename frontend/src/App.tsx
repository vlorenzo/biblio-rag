import ChatPage from './pages/ChatPage';
import { I18nProvider } from './i18n';

function App() {
  return (
    <div className="min-h-screen bg-archive-gray-50">
      <I18nProvider>
        <ChatPage />
      </I18nProvider>
    </div>
  );
}

export default App; 