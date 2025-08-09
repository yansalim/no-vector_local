from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from typing import List
import asyncio
import json
import uuid
from datetime import datetime
import shutil
from pathlib import Path
import os

from models import ChatRequest, ChatResponse, UploadResponse, SessionData
from pdf_processor import PDFProcessor
from llm_service import LLMService

app = FastAPI(title="PDF Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
    ],  # Next.js dev server on various ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_processor = PDFProcessor()
llm_service = LLMService()

# Storage directories
UPLOAD_DIR = Path("uploads")
SESSION_DIR = Path("sessions")
UPLOAD_DIR.mkdir(exist_ok=True)
SESSION_DIR.mkdir(exist_ok=True)

# In-memory storage for sessions (in production, use a database)
sessions = {}


@app.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...), description: str = Form(...)
):
    """Upload PDF documents and create a session"""

    if len(files) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 documents allowed")

    # Validate file types
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Create session
    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    # Save files and process them
    document_info = []
    for file in files:
        file_path = session_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text from PDF
        try:
            pages = pdf_processor.extract_pages(str(file_path))
            document_info.append(
                {
                    "filename": file.filename,
                    "path": str(file_path),
                    "pages": pages,
                    "total_pages": len(pages),
                }
            )
        except Exception as e:
            print(f"PDF processing error for {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error processing {file.filename}: {str(e)}"
            )

    # Store session data
    session_data = SessionData(
        session_id=session_id,
        description=description,
        documents=document_info,
        created_at=datetime.now(),
    )

    sessions[session_id] = session_data

    # Save session to disk
    session_file = SESSION_DIR / f"{session_id}.json"
    with open(session_file, "w") as f:
        # Convert datetime objects to strings manually
        session_dict = session_data.model_dump()
        session_dict["created_at"] = session_dict["created_at"].isoformat()
        json.dump(session_dict, f)

    return UploadResponse(
        session_id=session_id, message=f"Successfully uploaded {len(files)} documents"
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Handle chat requests with streaming response"""
    import time

    start_time = time.time()
    print(f"🌊 Streaming chat request started for session: {request.session_id}")
    print(f"📝 Question: {request.question}")

    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = sessions[request.session_id]
    print(f"📊 Found session with {len(session_data.documents)} documents")

    async def stream_response():
        try:
            total_cost = 0.0

            # Step 1: Select relevant documents based on description and question
            step1_start = time.time()
            print(f"⏱️ Step 1: Starting document selection...")
            selected_docs, step1_cost = await llm_service.select_documents(
                session_data.description,
                session_data.documents,
                request.question,
                request.chat_history,
            )
            total_cost += step1_cost
            step1_time = time.time() - step1_start
            print(f"✅ Step 1: Document selection completed in {step1_time:.2f}s")
            print(
                f"📑 Selected {len(selected_docs)} documents: {[doc['filename'] for doc in selected_docs]}"
            )

            # Step 2: Find relevant pages in selected documents (parallelized)
            step2_start = time.time()
            print(f"⏱️ Step 2: Starting parallel page relevance detection...")

            # Create tasks for parallel processing of all documents
            doc_tasks = []
            for i, doc in enumerate(selected_docs):
                print(
                    f"📖 Queuing document {i+1}/{len(selected_docs)}: {doc['filename']} ({len(doc['pages'])} pages)"
                )
                task = llm_service.find_relevant_pages(
                    doc["pages"],
                    request.question,
                    doc["filename"],
                    request.chat_history,
                )
                doc_tasks.append(task)

            # Execute all document processing in parallel
            print(f"🚀 Processing {len(doc_tasks)} documents in parallel...")
            doc_results = await asyncio.gather(*doc_tasks, return_exceptions=True)

            # Combine results
            relevant_pages = []
            step2_cost = 0.0
            for i, result in enumerate(doc_results):
                if isinstance(result, Exception):
                    print(
                        f"❌ Error processing {selected_docs[i]['filename']}: {result}"
                    )
                    continue
                if isinstance(result, tuple) and len(result) == 2:
                    pages, cost = result
                    step2_cost += cost
                    print(
                        f"✅ Document {selected_docs[i]['filename']}: {len(pages)} relevant pages"
                    )
                    relevant_pages.extend(pages)
                elif isinstance(result, list):
                    # Fallback for old format
                    print(
                        f"✅ Document {selected_docs[i]['filename']}: {len(result)} relevant pages"
                    )
                    relevant_pages.extend(result)

            step2_time = time.time() - step2_start
            total_cost += step2_cost
            print(f"✅ Step 2: Parallel page detection completed in {step2_time:.2f}s")
            print(f"📄 Total relevant pages found: {len(relevant_pages)}")

            # Send metadata first
            metadata = {
                "type": "metadata",
                "selected_documents": [doc["filename"] for doc in selected_docs],
                "relevant_pages_count": len(relevant_pages),
                "timing": {
                    "document_selection": step1_time,
                    "page_detection": step2_time,
                },
                "cost": total_cost,
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # Step 3: Stream the answer generation
            step3_start = time.time()
            print(f"⏱️ Step 3: Starting streaming answer generation...")

            async for chunk in llm_service.generate_answer_stream(
                relevant_pages, request.question, request.chat_history
            ):
                chunk_data = {"type": "content", "content": chunk}
                yield f"data: {json.dumps(chunk_data)}\n\n"

            step3_time = time.time() - step3_start
            total_time = time.time() - start_time
            print(
                f"✅ Step 3: Streaming answer generation completed in {step3_time:.2f}s"
            )
            print(f"🏁 Streaming chat request completed in {total_time:.2f}s total")
            print(
                f"📊 Timing breakdown: Doc Selection: {step1_time:.2f}s | Page Detection: {step2_time:.2f}s | Answer Gen: {step3_time:.2f}s"
            )

            # Update session cost
            session_data.total_session_cost = (
                session_data.total_session_cost or 0.0
            ) + total_cost

            # Send final metadata
            final_metadata = {
                "type": "complete",
                "total_time": total_time,
                "total_cost": total_cost,
                "session_cost": session_data.total_session_cost,
                "timing_breakdown": {
                    "document_selection": step1_time,
                    "page_detection": step2_time,
                    "answer_generation": step3_time,
                },
            }
            yield f"data: {json.dumps(final_metadata)}\n\n"

        except Exception as e:
            error_time = time.time() - start_time
            print(f"❌ Streaming chat request failed after {error_time:.2f}s: {str(e)}")
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = sessions[session_id]
    return {
        "session_id": session_id,
        "description": session_data.description,
        "documents": session_data.documents,  # Return full document data including pages
        "created_at": session_data.created_at,
        "total_session_cost": session_data.total_session_cost or 0.0,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/pdf/{session_id}/{filename}")
async def serve_pdf(session_id: str, filename: str):
    """Serve PDF files for viewing"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Construct file path
    file_path = os.path.join("uploads", session_id, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
