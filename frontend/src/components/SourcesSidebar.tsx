import { X, BookOpen, Calendar } from 'lucide-react';
import type { Citation } from '../types';

interface SourcesSidebarProps {
  isOpen: boolean;
  citations: Map<string, Citation>;
  onClose: () => void;
}

export default function SourcesSidebar({ isOpen, citations, onClose }: SourcesSidebarProps) {
  const citationsList = Array.from(citations.values());

  const getDocumentTypeIcon = (documentClass?: string) => {
    switch (documentClass) {
      case 'authored_by_subject':
        return <BookOpen className="w-4 h-4 text-archive-blue-600" />;
      case 'subject_library':
        return <BookOpen className="w-4 h-4 text-green-600" />;
      case 'about_subject':
        return <BookOpen className="w-4 h-4 text-purple-600" />;
      case 'subject_traces':
        return <BookOpen className="w-4 h-4 text-orange-600" />;
      default:
        return <BookOpen className="w-4 h-4 text-archive-gray-600" />;
    }
  };

  const getDocumentTypeLabel = (documentClass?: string) => {
    switch (documentClass) {
      case 'authored_by_subject':
        return 'Written by Artom';
      case 'subject_library':
        return 'From Artom\'s Library';
      case 'about_subject':
        return 'About Artom';
      case 'subject_traces':
        return 'Artom\'s Traces';
      default:
        return 'Document';
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed lg:relative top-0 right-0 h-full w-96 bg-white border-l border-archive-gray-200 
        transform transition-transform duration-300 ease-in-out z-50
        ${isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
        ${isOpen ? 'lg:block' : 'lg:hidden'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-archive-gray-200">
            <h2 className="text-lg font-serif font-semibold text-archive-gray-900">
              Sources & Citations
            </h2>
            <button
              onClick={onClose}
              className="p-1 text-archive-gray-400 hover:text-archive-gray-600 rounded"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {citationsList.length === 0 ? (
              <div className="text-center py-8">
                <BookOpen className="w-12 h-12 text-archive-gray-300 mx-auto mb-4" />
                <p className="text-archive-gray-500">
                  Citations will appear here when you ask questions about the archive.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {citationsList.map((citation, index) => (
                  <div 
                    key={citation.id}
                    className="bg-archive-gray-50 rounded-lg p-4 border border-archive-gray-100"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1">
                        {getDocumentTypeIcon(citation.document_class)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-medium text-archive-gray-900 text-sm">
                            {citation.title}
                          </h3>
                          <span className="text-xs bg-archive-blue-100 text-archive-blue-800 px-2 py-1 rounded">
                            [{index + 1}]
                          </span>
                        </div>
                        
                        {citation.author && (
                          <p className="text-sm text-archive-gray-600 mb-2">
                            by {citation.author}
                          </p>
                        )}
                        
                        <div className="flex items-center space-x-4 text-xs text-archive-gray-500 mb-3">
                          <span className="flex items-center space-x-1">
                            <span>{getDocumentTypeLabel(citation.document_class)}</span>
                          </span>
                          
                          {citation.publication_year && (
                            <span className="flex items-center space-x-1">
                              <Calendar className="w-3 h-3" />
                              <span>{citation.publication_year}</span>
                            </span>
                          )}
                        </div>
                        
                        {citation.excerpt && (
                          <blockquote className="text-sm text-archive-gray-700 border-l-2 border-archive-blue-200 pl-3 italic">
                            "{citation.excerpt}"
                          </blockquote>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Footer */}
          {citationsList.length > 0 && (
            <div className="p-4 border-t border-archive-gray-200 bg-archive-gray-50">
              <p className="text-xs text-archive-gray-500 text-center">
                {citationsList.length} source{citationsList.length !== 1 ? 's' : ''} found
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
} 