'use client';

import { useState, useEffect } from 'react';
import StatelessChatSection from './components/StatelessChatSection';

interface DocumentData {
  id: number;
  filename: string;
  pages: Array<{
    page_number: number;
    text: string;
  }>;
  total_pages: number;
}

export default function Home() {
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [description, setDescription] = useState('');

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const savedDocuments = localStorage.getItem('chatbot_documents');
      const savedDescription = localStorage.getItem('chatbot_description');
      
      if (savedDocuments) {
        const parsedDocuments = JSON.parse(savedDocuments);
        if (Array.isArray(parsedDocuments)) {
          setDocuments(parsedDocuments);
        } else {
          console.warn('Invalid documents format in localStorage, clearing...');
          localStorage.removeItem('chatbot_documents');
          setDocuments([]);
        }
      }
      if (savedDescription) {
        setDescription(savedDescription);
      }
    } catch (error) {
      console.error('Error loading from localStorage:', error);
    }
  }, []);

  // Save to localStorage whenever documents or description changes
  useEffect(() => {
    try {
      if (documents.length > 0) {
        localStorage.setItem('chatbot_documents', JSON.stringify(documents));
      }
      if (description) {
        localStorage.setItem('chatbot_description', description);
      }
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }, [documents, description]);

  const handleReset = () => {
    setDocuments([]);
    setDescription('');
    try {
      localStorage.removeItem('chatbot_documents');
      localStorage.removeItem('chatbot_description');
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  };

  const handleUpdateDocuments = (newDocuments: DocumentData[]) => {
    console.log('handleUpdateDocuments called with:', newDocuments);
    
    // Validate input
    if (!Array.isArray(newDocuments)) {
      console.error('newDocuments is not an array:', newDocuments);
      return;
    }
    
    setDocuments(newDocuments);
  };

  const handleUpdateDescription = (newDescription: string) => {
    setDescription(newDescription);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            PDF Document Chatbot
          </h1>
          <p className="text-gray-600">
            Upload PDFs and ask questions about their content - completely stateless and secure
          </p>
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
