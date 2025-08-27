import React, { useMemo } from 'react';
import StatelessChatSection from '../app/components/StatelessChatSection';
import GitHubIcon from '../app/components/GitHubIcon';
import { usePersistentState } from '../app/hooks/usePersistentState';

interface DocumentData {
  id: number;
  filename: string;
  pages: { page_number: number; text: string }[];
  total_pages: number;
}

export default function App() {
  const [documents, setDocuments] = usePersistentState<DocumentData[]>('chatbot_documents', []);
  const [description, setDescription] = usePersistentState<string>('chatbot_description', '');

  const handleReset = () => {
    setDocuments([]);
    setDescription('');
    try {
      localStorage.removeItem('chatbot_documents');
      localStorage.removeItem('chatbot_description');
    } catch {}
  };

  const handleUpdateDocuments = (newDocuments: DocumentData[]) => {
    if (!Array.isArray(newDocuments)) return;
    setDocuments(newDocuments);
  };

  const handleUpdateDescription = (newDescription: string) => {
    setDescription(newDescription);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8 relative">
          <a
            href="https://github.com/yansalim/no-vector_local/"
            target="_blank"
            rel="noopener noreferrer"
            className="absolute top-0 right-0 text-gray-600 hover:text-gray-900 transition-colors flex items-center space-x-2 group"
            title="Star us on GitHub"
          >
            <span className="text-sm font-medium group-hover:text-gray-900 transition-colors">
              Star us
            </span>
            <GitHubIcon className="w-8 h-8" />
          </a>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">No-Vector PDF Chat</h1>
          <p className="text-gray-600">Chat with your PDF, no vector needed.</p>
        </div>

        <div className="max-w-6xl mx-auto h-[80vh]">
          <StatelessChatSection
            documents={documents}
            description={description}
            onReset={handleReset}
            onUpdateDocuments={handleUpdateDocuments}
            onUpdateDescription={handleUpdateDescription}
          />
        </div>
      </div>
    </main>
  );
}


