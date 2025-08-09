'use client';

import { useState } from 'react';
import UploadSection from './components/UploadSection';
import ChatSection from './components/ChatSection';

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUploadSuccess = (newSessionId: string) => {
    setSessionId(newSessionId);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Vectorless PDF Chatbot
          </h1>
          <p className="text-gray-600">
            Upload your PDF documents and ask questions about them
          </p>
        </header>

        {!sessionId ? (
          <UploadSection 
            onUploadSuccess={handleUploadSuccess}
            isUploading={isUploading}
            setIsUploading={setIsUploading}
          />
        ) : (
          <ChatSection 
            sessionId={sessionId}
            onReset={() => setSessionId(null)}
          />
        )}
      </div>
    </div>
  );
}
