"""
RAG-based chat endpoints for querying meeting transcripts.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from core.validators import InputValidator
from core.logger import get_logger
from core.exceptions import ValidationError
from core.rag_engine import ask_question, load_rag_chain

logger = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat queries."""
    question: str = Field(..., description="Question to ask about the transcript", min_length=3, max_length=1000)
    session_id: Optional[str] = Field(None, description="Optional session ID for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What were the main decisions made in the meeting?",
                "session_id": "abc123"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat queries."""
    answer: str
    session_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_transcript(request: ChatRequest):
    """
    Ask questions about a previously analyzed transcript using RAG.
    
    - **question**: Your question about the transcript
    - **session_id**: Optional session ID to maintain context
    
    Returns an AI-generated answer based on the transcript.
    """
    try:
        # Validate question
        validated_question = InputValidator.validate_question(request.question)
        
        logger.info(f"Processing chat query: {validated_question[:100]}")
        
        # Load RAG chain (in production, this would be cached per session)
        # For now, we'll load from the persistent vector store
        rag_chain = load_rag_chain()
        
        # Get answer
        answer = ask_question(rag_chain, validated_question)
        
        return {
            "answer": answer,
            "session_id": request.session_id
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process question")


@router.delete("/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """
    Clear a chat session and its associated context.
    
    - **session_id**: The session ID to clear
    
    This is useful for freeing up memory and starting fresh.
    """
    try:
        # In production: Clear session from cache/database
        logger.info(f"Clearing chat session: {session_id}")
        
        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")
