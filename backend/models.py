from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    question: str
    chat_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    answer: str
    selected_documents: List[str]
    relevant_pages_count: int
    total_cost: Optional[float] = 0.0


class UploadResponse(BaseModel):
    session_id: str
    message: str


class SessionData(BaseModel):
    session_id: str
    description: str
    documents: List[Dict[str, Any]]
    created_at: datetime
    total_session_cost: Optional[float] = 0.0
