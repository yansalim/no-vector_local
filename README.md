# No-Vector PDF Chat

A revolutionary PDF chatbot that uses **no vector embeddings** or traditional RAG. Instead, it leverages Large Language Models for intelligent document selection and page relevance detection, providing a completely stateless and privacy-first experience.

## 🚀 What Makes This "No-Vector"?

Traditional PDF chatbots convert documents into vector embeddings for semantic search. This approach:
- ❌ **Requires expensive vector databases**
- ❌ **Needs pre-processing and indexing**
- ❌ **Stores document data on servers**
- ❌ **Loses context and nuance in embeddings**

Our **No-Vector** approach:
- ✅ **Uses LLM reasoning instead of vectors**
- ✅ **Processes documents in real-time**
- ✅ **Completely stateless - no server storage**
- ✅ **Preserves full document context**
- ✅ **Privacy-first - documents stay in your browser**

## 🧠 How the No-Vector Process Works

### 3-Step Intelligent Document Analysis

```mermaid
graph TD
    A[📄 User uploads PDFs] --> B[🧠 LLM Document Selection]
    B --> C[🎯 LLM Page Relevance Detection]
    C --> D[💬 Contextual Answer Generation]
    
    B --> B1[Analyzes collection description<br/>+ document filenames<br/>+ user question]
    C --> C1[Examines actual page content<br/>from selected documents<br/>in parallel processing]
    D --> D1[Generates comprehensive answer<br/>with proper citations]
```

### Step 1: 🧠 **Smart Document Selection**
- LLM reads your collection description and document filenames
- Intelligently selects which documents are likely to contain relevant information
- No embeddings needed - uses reasoning and context understanding

### Step 2: 🎯 **Page Relevance Detection**
- LLM examines actual page content from selected documents
- Processes multiple documents in parallel for speed
- Identifies the most relevant pages based on question context

### Step 3: 💬 **Contextual Answer Generation**
- Uses only the relevant pages to generate accurate answers
- Maintains full document context and nuance
- Provides proper citations and references

## ✨ Key Features

### 🔒 **Privacy-First & Stateless**
- **Zero Server Storage**: Documents processed and stored entirely in your browser
- **LocalStorage Persistence**: Your documents persist across browser sessions
- **No Data Leakage**: Document content never persists on servers


### 📁 **Advanced File Handling**
- **Up to 100 PDF documents** per session
- **Chunked Upload System**: Automatically handles large file sets (>4.5MB)
- **4.5MB per file limit** - processes substantial documents
- **Real-time Processing**: No pre-indexing required

### 💡 **Intelligent Processing**
- **Multi-Model Support**: GPT-5 GPT-5-mini, and more
- **Parallel Processing**: Multiple documents analyzed simultaneously
- **Context Preservation**: Full document context maintained throughout
- **Dynamic Descriptions**: Edit collection descriptions anytime

### 🎨 **Modern Interface**
- **Responsive Design**: Works on desktop and mobile
- **Real-time Progress**: Visual feedback during uploads and processing
- **GitHub Integration**: Easy access to source code
- **Error Handling**: Comprehensive error messages and recovery

## 🛠 Technology Stack

### Frontend
- **React + Vite**: SPA build with lightning-fast dev server and static output
- **TypeScript**: Type safety and better DX
- **Tailwind CSS**: Utility-first styling (via PostCSS plugin)
- **Lucide React**: Clean, consistent icon set

### Backend (FastAPI)
- **FastAPI + Uvicorn**: High-performance Python API
- **PyPDF2**: Robust PDF text extraction
- **OpenAI**: LLM reasoning for doc/page selection and answers
- **Chunked Processing**: Efficient multi-file uploads

### Infrastructure
- **Docker Compose**: One command to run frontend (Nginx) and backend
- **No Databases**: Completely stateless architecture
- **Nginx**: Serves built React app and proxies API

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+ (if you need to start the backend manually)
- Docker (optional, to run with containers)
- OpenAI API key (required for full functionality)

### 1. Clone and Install
```bash
git clone https://github.com/yansalim/no-vector_local.git
cd no-vector_local
npm install
```

### 2. Environment Setup
- Frontend (dev): uses `VITE_API_BASE_URL` to point to the backend
- Backend: uses `OPENAI_API_KEY` (required)

Create `.env` in the backend's root directory (or export the variable):
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run Locally (with Node)
```bash
# starts frontend (Vite) + backend (Uvicorn) in parallel (Windows-friendly)
npm run dev

# frontend only (port 3000)
npm run web

# backend only (port 8000)
npm run backend:win
```
Visit http://localhost:3000 (or 3001 if 3000 is in use)

If the backend is at a different URL on your machine, export it before building the frontend:
```bash
set VITE_API_BASE_URL=http://localhost:8000 && npm run web
```

### 4. Running with Docker (recommended)
```bash
docker compose build --no-cache
docker compose up -d
```
Useful environment variables (via docker-compose.yml):
- `BACKEND_URL` (passed to the build as `VITE_API_BASE_URL` for the frontend)
- `OPENAI_API_KEY` (backend)

URLs:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/health

## 📖 How to Use

### 1. **Upload Your Documents**
- Click "Add Your First Document" or "Add Files"
- Select up to 100 PDF files (4.5MB each max)
- Add a description of your document collection
- Large uploads are automatically chunked for reliability

### 2. **Start Chatting**
- Ask questions about your documents in natural language
- Watch the 3-step process: Document Selection → Page Detection → Answer Generation
- Get detailed answers with timing and cost breakdowns

### 3. **Manage Your Collection**
- Add more documents anytime
- Edit collection descriptions
- Start new sessions as needed
- All data stays in your browser

## 🏗 Architecture Deep Dive

### Stateless Design
```
┌─────────────────┐    ┌───────────────┐    ┌─────────────────┐
│   Browser       │    │   FastAPI     │    │   OpenAI API    │
│                 │    │               │    │                 │
│ • LocalStorage  │◄──►│ • /upload     │◄──►│ • GPT Models    │
│ • Document Data │    │ • /chat/stream│    │ • Real-time     │
│ • Chat History  │    │ • /health     │    │   Processing    │
│ • Session State │    │ • Stateless   │    │                 │
└─────────────────┘    └───────────────┘    └─────────────────┘
```

### Chunked Upload System
When uploading large document sets:
1. **Size Detection**: Frontend calculates total upload size
2. **Automatic Chunking**: Splits into 3.5MB chunks if needed
3. **Parallel Processing**: Each chunk processed independently
4. **Progressive Results**: Documents become available as chunks complete
5. **Error Recovery**: Failed chunks can be retried individually

## 🔧 API Endpoints (FastAPI)

### `POST /upload`
Upload and process PDF documents
- **Input**: FormData with files and description
- **Output**: Processed documents with extracted text
- **Features**: Automatic chunking, progress tracking

### `POST /chat/stream`
Stream chat responses in real-time
- **Input**: Question, documents, chat history
- **Output**: Server-sent events with processing steps
- **Features**: Real-time progress, cost tracking, citations

### `GET /health`
Service health check
- **Output**: System status and mode information

## 🎯 Advantages Over Traditional RAG

| Traditional RAG | No-Vector Approach |
|----------------|---------------------|
| 🗄️ Requires vector database | 🚫 No database needed |
| 📊 Pre-processes to embeddings | 🔄 Real-time processing |
| 💰 Expensive infrastructure | 💸 Serverless & cost-effective |
| 🔒 Stores data on servers | 🛡️ Browser-only storage |
| 📏 Limited by embedding dimensions | 🧠 Full context understanding |
| ⚡ Fast retrieval, lossy context | 🎯 Accurate reasoning, full context |

## 🌟 Example Workflow

1. **Upload**: Marketing team uploads 50 company PDFs
2. **Describe**: "Company policies, procedures, and guidelines"
3. **Ask**: "What is our remote work policy?"
4. **Process**:
   - 🧠 LLM selects "HR Handbook" and "Remote Work Guidelines"
   - 🎯 Identifies relevant pages about remote work
   - 💬 Generates comprehensive answer with citations
5. **Result**: Accurate answer in ~15 seconds with cost breakdown

## 🔮 Future Enhancements

- **Multi-format Support**: Word docs, PowerPoint, Excel
- **Advanced Citations**: Highlight exact text passages
- **Collaboration Features**: Share sessions with team members
- **Analytics Dashboard**: Usage patterns and insights
- **Custom Models**: Support for local and custom LLMs
- **Batch Operations**: Process multiple questions simultaneously

## 🤝 Contributing

We welcome contributions! This project showcases how modern LLMs can replace traditional vector-based approaches while providing better accuracy and user experience.

## 📄 License

MIT License - see LICENSE file for details.

---

⭐ **Star us on GitHub** if you find this no-vector approach interesting!

Built with ❤️ by [ROE AI Inc.](https://github.com/yansalim/)