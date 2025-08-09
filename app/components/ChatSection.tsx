'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import dynamic from 'next/dynamic';

// Dynamically import react-pdf components to avoid SSR issues
const Document = dynamic(
  () => import('react-pdf').then((mod) => mod.Document),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading PDF viewer...</span>
      </div>
    )
  }
);

const Page = dynamic(
  () => import('react-pdf').then((mod) => mod.Page),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    )
  }
);

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  progress?: {
    status: string;
    step: number;
    total: number;
    stepCost?: number;
    stepTime?: number;
  };
  metadata?: {
    selectedDocuments?: Array<{id: number, filename: string}>;
    relevantPagesCount?: number;
    timing?: {
      document_selection?: number;
      page_detection?: number;
      answer_generation?: number;
      total_time?: number;
    };
    costs?: {
      document_selection?: number;
      page_detection?: number;
      answer_generation?: number;
      total_cost?: number;
    };
    model?: string;
  };
}

interface ChatSectionProps {
  sessionId: string;
  onReset: () => void;
}

export default function ChatSection({ sessionId, onReset }: ChatSectionProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [showDocuments, setShowDocuments] = useState(true);
  const [selectedPage, setSelectedPage] = useState<{content: string, pageNumber: number, filename: string, sessionId: string} | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [totalSessionCost, setTotalSessionCost] = useState<number>(0);
  const [selectedModel, setSelectedModel] = useState<string>('gpt-5-mini');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Import PDF.js worker setup only on client side
  useEffect(() => {
    if (typeof window !== 'undefined') {
      import('react-pdf').then((pdfjs) => {
        pdfjs.pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.pdfjs.version}/build/pdf.worker.min.mjs`;
      });
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Fetch session info
    fetchSessionInfo();
  }, [sessionId]);

  const fetchSessionInfo = async () => {
    try {
      const response = await fetch(`http://localhost:8000/session/${sessionId}`);
      if (response.ok) {
        const info = await response.json();
        setSessionInfo(info);

        setTotalSessionCost(info.total_session_cost || 0);
      }
    } catch (error) {
      console.error('Error fetching session info:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!currentQuestion.trim() || isLoading) return;

    const question = currentQuestion;
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentQuestion('');
    setIsLoading(true);

    // Create assistant message placeholder for streaming
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      progress: {
        status: 'Starting...',
        step: 0,
        total: 3,
      },
      metadata: {
        selectedDocuments: [],
        relevantPagesCount: 0,
      },
    };
    
    setMessages(prev => [...prev, assistantMessage]);

    try {
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: question,
          model: selectedModel,
          chat_history: messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp.toISOString()
          }))
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No reader available');
      }

      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'status') {
                // Update progress status in the message
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? {
                        ...msg,
                        progress: {
                          status: data.message,
                          step: data.step_number,
                          total: data.total_steps,
                        }
                      }
                    : msg
                ));
              } else if (data.type === 'step_complete') {
                // Step completed - update progress and metadata
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? {
                        ...msg,
                        progress: {
                          ...msg.progress!,
                          stepCost: data.cost,
                          stepTime: data.time_taken,
                        },
                        metadata: {
                          ...msg.metadata,
                          ...(data.step === 'document_selection' && {
                            selectedDocuments: data.selected_documents,
                          }),
                          ...(data.step === 'page_selection' && {
                            relevantPagesCount: data.relevant_pages_count,
                          }),
                        }
                      }
                    : msg
                ));
              } else if (data.type === 'content') {
                // Append content
                accumulatedContent += data.content;
                
                // Track page markers during streaming
                
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: accumulatedContent }
                    : msg
                ));
              } else if (data.type === 'complete') {
                // Streaming complete - update session cost and final metadata
                if (data.session_cost !== undefined) {
                  setTotalSessionCost(data.session_cost);
                }
                
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? {
                        ...msg,
                        isStreaming: false,
                        progress: undefined,
                        metadata: {
                          ...msg.metadata,
                          timing: data.timing_breakdown,
                          costs: data.cost_breakdown,
                          model: selectedModel
                        }
                      }
                    : msg
                ));
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? {
              ...msg,
              content: 'Sorry, I encountered an error while processing your question. Please try again.',
              isStreaming: false,
              progress: undefined
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handlePageReference = (filename: string, pageNumber: number) => {
    if (!sessionInfo) {
      console.error('No session info available');
      return;
    }
    

    
    // Find the document and page
    const document = sessionInfo.documents.find((doc: any) => doc.filename === filename);
    if (!document) {
      console.error('Document not found:', filename);
      return;
    }
    

    
    if (!document.pages || !Array.isArray(document.pages)) {
      console.error('Document pages not available or not an array:', document.pages);
      return;
    }
    
    const page = document.pages.find((p: any) => p.page_number === pageNumber);
    if (!page) {
      console.error('Page not found:', pageNumber, 'Available pages:', document.pages.map((p: any) => p.page_number));
      return;
    }
    

    
    setSelectedPage({
      content: page.text,
      pageNumber: pageNumber,
      filename: filename,
      sessionId: sessionId
    });
  };

  // Function to process page references in content before markdown
  const processPageReferences = (content: string): string => {
    if (!content.includes('$PAGE_START')) {
      return content;
    }
    
    // Parse special markers: $PAGE_STARTfilename:pages$PAGE_END
    const pageRefRegex = /\$PAGE_START([^:]+):([^\$]+)\$PAGE_END/g;
    
    // Replace markers with markdown links
    const processedContent = content.replace(pageRefRegex, (match, filename, pageSpec) => {
      const cleanFilename = filename.trim();
      const cleanPageSpec = pageSpec.trim();
      
      // Convert to markdown link format with special data attributes
      return `[${cleanFilename} (Page ${cleanPageSpec})](javascript:void(0) "data-pdf-ref=${cleanFilename}:${cleanPageSpec}")`;
    });
    
    return processedContent;
  };



   

  // Helper function to parse page specifications like "5", "2,7,12", "15-18"
  const parsePageSpecification = (pageSpec: string): number[] => {
    const pages: number[] = [];
    
    // Split by commas for multiple pages/ranges
    const parts = pageSpec.split(',');
    
    parts.forEach(part => {
      part = part.trim();
      
      if (part.includes('-')) {
        // Handle range like "15-18"
        const [start, end] = part.split('-').map(p => parseInt(p.trim()));
        if (start && end && start <= end) {
          for (let i = start; i <= end; i++) {
            pages.push(i);
          }
        }
      } else {
        // Handle single page
        const pageNum = parseInt(part);
        if (pageNum) {
          pages.push(pageNum);
        }
      }
    });
    
    return pages;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg h-screen flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex justify-between items-center mb-3">
          <div>
            <h2 className="text-xl font-semibold text-gray-800">Chat with your documents</h2>
            {sessionInfo && (
              <p className="text-sm text-gray-600">
                {sessionInfo.documents.length} document(s) • {sessionInfo.description}
              </p>
            )}
          </div>
          <button
            onClick={onReset}
            className="text-gray-500 hover:text-gray-700 px-3 py-1 rounded border border-gray-300 hover:border-gray-400"
          >
            Upload New Documents
          </button>
        </div>
        
        {/* Document List */}
        {sessionInfo && sessionInfo.documents.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <button
                onClick={() => setShowDocuments(!showDocuments)}
                className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                <span>Uploaded Documents</span>
                <svg
                  className={`w-4 h-4 transition-transform ${showDocuments ? 'rotate-90' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <div className="flex items-center space-x-3">
                <span className="text-xs text-gray-500">{sessionInfo.documents.length} files</span>
                <span className="text-xs font-medium text-green-600">
                  Cost: ${totalSessionCost.toFixed(4)}
                </span>
              </div>
            </div>
            {showDocuments && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {sessionInfo.documents.map((doc: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center space-x-2 bg-white p-2 rounded border border-gray-200"
                >
                  <div className="flex-shrink-0">
                    <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-700 truncate" title={doc.filename}>
                      ID {doc.id}: {doc.filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {doc.total_pages} pages
                    </p>
                  </div>
                </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p>Ask me anything about your uploaded documents!</p>
            <p className="text-sm mt-2">Examples:</p>
            <ul className="text-sm mt-1 space-y-1">
              <li>• "What are the main topics covered?"</li>
              <li>• "Summarize the key findings"</li>
              <li>• "What does it say about [specific topic]?"</li>
            </ul>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {/* Progress indicator for streaming messages */}
              {message.isStreaming && message.progress && (
                <div className="mb-3 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-sm font-medium text-blue-800">
                      {message.progress.status}
                    </span>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${(message.progress.step / message.progress.total) * 100}%` }}
                    ></div>
                  </div>
                  
                  <div className="flex justify-between text-xs text-blue-600">
                    <span>Step {message.progress.step} of {message.progress.total}</span>
                    {message.progress.stepTime && message.progress.stepCost && (
                      <span>{message.progress.stepTime.toFixed(2)}s • ${message.progress.stepCost.toFixed(4)}</span>
                    )}
                  </div>
                </div>
              )}

              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  components={{
                    // Custom styling for markdown elements
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    a: ({ href, title, children }) => {
                      // Handle PDF reference links
                      if (title && title.startsWith('data-pdf-ref=')) {
                        const pdfRef = title.replace('data-pdf-ref=', '');
                        const [filename, pageSpec] = pdfRef.split(':');
                        const pages = parsePageSpecification(pageSpec);
                        
                        if (pages.length > 0) {
                          const pageNum = pages[0]; // Use first page for click
                          return (
                            <button
                              onClick={() => handlePageReference(filename, pageNum)}
                              className="text-blue-600 hover:text-blue-800 underline font-medium cursor-pointer mx-0.5"
                              title={`View ${filename} - Page ${pageNum}`}
                            >
                              {children}
                            </button>
                          );
                        }
                      }
                      
                      // Regular links
                      return (
                        <a href={href} title={title} className="text-blue-600 hover:text-blue-800 underline">
                          {children}
                        </a>
                      );
                    },
                    h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                    ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    code: ({ children, ...props }) => {
                      const isInline = !props.className?.includes('language-');
                      const bgColor = message.role === 'user' ? 'bg-blue-700 bg-opacity-50' : 'bg-gray-200';
                      return isInline ? (
                        <code className={`${bgColor} px-1 rounded text-xs font-mono`}>{children}</code>
                      ) : (
                        <code className={`block ${bgColor} p-2 rounded text-xs font-mono whitespace-pre-wrap`}>{children}</code>
                      );
                    },
                    pre: ({ children }) => {
                      const bgColor = message.role === 'user' ? 'bg-blue-700 bg-opacity-50' : 'bg-gray-200';
                      return <pre className={`${bgColor} p-2 rounded mb-2 overflow-x-auto`}>{children}</pre>;
                    },
                    blockquote: ({ children }) => {
                      const borderColor = message.role === 'user' ? 'border-blue-300' : 'border-gray-300';
                      return <blockquote className={`border-l-4 ${borderColor} pl-3 italic`}>{children}</blockquote>;
                    },
                    strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                  }}
                >
                  {processPageReferences(message.content)}
                </ReactMarkdown>
              </div>
              {message.metadata && (
                <div className="mt-2 text-xs opacity-60 space-y-1">
                  <div className="flex flex-wrap gap-x-4 gap-y-1">
                    {message.metadata.selectedDocuments && (
                      <span><span className="font-medium">Docs:</span> {message.metadata.selectedDocuments.map(doc => `${doc.filename} (ID: ${doc.id})`).join(', ')}</span>
                    )}
                    {message.metadata.relevantPagesCount && (
                      <span><span className="font-medium">Pages:</span> {message.metadata.relevantPagesCount}</span>
                    )}
                    {message.metadata.model && (
                      <span><span className="font-medium">Model:</span> {message.metadata.model}</span>
                    )}
                    {message.metadata.timing?.total_time && (
                      <span><span className="font-medium">Time:</span> {message.metadata.timing.total_time.toFixed(1)}s</span>
                    )}
                    {message.metadata.costs?.total_cost && (
                      <span><span className="font-medium">Cost:</span> ${message.metadata.costs.total_cost.toFixed(4)}</span>
                    )}
                  </div>
                </div>
              )}
              <p className={`text-xs mt-1 ${
                message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}



        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        {/* Model Selection */}
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            AI Model:
          </label>
          <div className="flex space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name="model"
                value="gpt-5-mini"
                checked={selectedModel === 'gpt-5-mini'}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isLoading}
                className="text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">GPT-5 Mini (Faster, Lower Cost)</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name="model"
                value="gpt-5"
                checked={selectedModel === 'gpt-5'}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isLoading}
                className="text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">GPT-5 (Higher Quality, Higher Cost)</span>
            </label>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <textarea
            value={currentQuestion}
            onChange={(e) => setCurrentQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your documents..."
            className="flex-1 px-3 py-2 text-gray-700 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!currentQuestion.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>

      {/* Page Content Modal */}
      {selectedPage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-[80vh] w-full flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  {selectedPage.filename} - Page {selectedPage.pageNumber}
                </h3>
              </div>
              <button
                onClick={() => setSelectedPage(null)}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 overflow-auto p-4 flex justify-center">
              <div className="max-w-full">
                <Document
                  file={`http://localhost:8000/pdf/${selectedPage.sessionId}/${selectedPage.filename}`}
                  onLoadSuccess={() => setPdfError(null)}
                  onLoadError={(error) => {
                    console.error('PDF load error:', error);
                    setPdfError(error.message || 'Failed to load PDF');
                  }}
                  loading={
                    <div className="flex items-center justify-center p-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <span className="ml-3 text-gray-600">Loading PDF...</span>
                    </div>
                  }
                  error={
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg max-w-md">
                      <h4 className="text-red-800 font-medium mb-2">Unable to load PDF</h4>
                      <p className="text-red-600 text-sm mb-3">
                        {pdfError || 'The PDF file could not be displayed. This might be due to CORS policy or network issues.'}
                      </p>
                      <details className="text-sm">
                        <summary className="cursor-pointer text-red-700 hover:text-red-900">Show extracted text instead</summary>
                        <div className="mt-3 p-3 bg-white rounded border text-gray-800 whitespace-pre-wrap max-h-64 overflow-y-auto text-xs leading-relaxed">
                          {selectedPage.content}
                        </div>
                      </details>
                    </div>
                  }
                >
                  <Page
                    pageNumber={selectedPage.pageNumber}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                    className="border border-gray-300 shadow-lg"
                    width={Math.min(800, window.innerWidth * 0.8)}
                    onLoadError={(error) => {
                      console.error('Page load error:', error);
                      setPdfError(`Failed to load page ${selectedPage.pageNumber}`);
                    }}
                  />
                </Document>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="flex justify-end p-4 border-t border-gray-200">
              <button
                onClick={() => setSelectedPage(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 