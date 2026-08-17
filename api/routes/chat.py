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
from main import get_rag_chain_for_source

logger = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat queries."""
    question: str = Field(..., description="Question to ask about the transcript", min_length=3, max_length=1000)
    session_id: Optional[str] = Field(None, description="Optional session/job ID for retrieving the right RAG chain")
    debug: bool = Field(False, description="Enable debug mode for query routing details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What were the main decisions made in the meeting?",
                "session_id": "abc123-job-id",
                "debug": False
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
    - **session_id**: Optional job ID or session ID to retrieve the correct RAG chain
    
    Returns an AI-generated answer based on the transcript.
    
    Note: If session_id is provided, uses the RAG chain from that specific analysis job.
    Otherwise, loads from persistent vector store (last analyzed transcript).
    """
    try:
        # Validate question
        validated_question = InputValidator.validate_question(request.question)
        
        logger.info(f"Processing chat query: {validated_question[:100]}")
        
        # Try to get RAG chain from session/job first
        rag_chain = None
        if request.session_id:
            rag_chain = get_rag_chain_for_source(request.session_id)
            logger.info(f"Retrieved RAG chain for session: {request.session_id}")
        
        # Fallback to persistent vector store if no session or not found
        if rag_chain is None:
            logger.info("Loading RAG chain from persistent vector store")
            rag_chain = load_rag_chain()
        
        if rag_chain is None:
            raise HTTPException(
                status_code=400,
                detail="No transcript available for chat. Please analyze a video first."
            )
        
        # Get answer
        answer = ask_question(rag_chain, validated_question, debug=request.debug)
        
        return {
            "answer": answer,
            "session_id": request.session_id
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
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
        
        # Clear from internal storage if exists
        from main import _rag_chain_store
        if session_id in _rag_chain_store:
            del _rag_chain_store[session_id]
            logger.info(f"Removed RAG chain for session: {session_id}")
        
        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")

