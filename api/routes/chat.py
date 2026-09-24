"""
RAG-based chat endpoints for querying meeting transcripts.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict

import os

from core.validators import InputValidator
from core.logger import get_logger
from core.exceptions import ValidationError
from core.auth_middleware import get_current_user, AuthUser
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
    sources: Optional[List[Dict[str, Any]]] = None
    query_type: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_transcript(
    request: ChatRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Ask questions about a previously analyzed transcript using intelligent RAG.
    
    - **question**: Your question about the transcript/document
    - **session_id**: Optional job ID or session ID to retrieve the correct RAG chain
    - **debug**: Enable debug logging for query routing
    
    Intelligent Query Routing:
    1. **Whole-content summarization**: For requests like "summarize", "give me 50-word summary", 
       "main points", "overview" - uses map-reduce over full content with constraint handling
    2. **Specific questions**: For targeted questions like "What is chapter 3 about?" - 
       uses semantic search (top-k retrieval) with LLM answering
    3. **Extraction**: For requests like "list all action items" - uses expanded retrieval
    
    Supports constraints:
    - Word limits: "Give me a 50-word summary"
    - Format: "Summarize in bullet points" or "numbered list"
    
    Returns an AI-generated answer based on the content.
    
    RAG Chain Retrieval Strategy:
    1. If session_id is provided, use that RAG chain only
    2. If the session is missing, return 404 (do not use another user's content)
    3. In development only, a missing session_id may use the most recent chain
    """
    try:
        # Validate question
        validated_question = InputValidator.validate_question(request.question)
        
        logger.info(f"[Chat] Processing query: {validated_question[:100]}...")
        
        rag_chain = None
        session_id = str(request.session_id).strip() if request.session_id else ""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        debug_mode = bool(request.debug) and environment != "production"
        
        if session_id:
            logger.info(f"[Chat] Looking for session: {session_id}")
            rag_chain = get_rag_chain_for_source(session_id)
            
            if rag_chain:
                logger.info(f"[Chat]   Found RAG chain for session: {session_id}")
            else:
                logger.warning(f"[Chat] No RAG chain found for session: {session_id}")
                raise HTTPException(
                    status_code=404,
                    detail="No transcript found for this session. Analyze the video or document again, then retry chat."
                )
        elif environment == "production":
            raise HTTPException(
                status_code=400,
                detail="session_id is required. Analyze a video or document first, then chat with that session."
            )
        else:
            from main import get_most_recent_rag_chain, list_all_rag_sessions
            logger.info("[Chat] No session_id provided, using most recent RAG chain (development only)")
            rag_chain = get_most_recent_rag_chain()
            
            if rag_chain:
                logger.info("[Chat]   Using most recent RAG chain")
            else:
                available_sessions = list_all_rag_sessions()
                logger.error(f"[Chat] No RAG chains available. Available sessions: {available_sessions}")
                raise HTTPException(
                    status_code=400,
                    detail="No transcript available for chat. Please analyze a video/document first."
                )
        
        # Get answer with intelligent routing (with timeout)
        import asyncio
        
        try:
            # Run with 60 second timeout
            answer_dict = await asyncio.wait_for(
                asyncio.to_thread(
                    rag_chain.ask, validated_question, 5, debug_mode
                ),
                timeout=60.0
            )
            if isinstance(answer_dict, str):
                answer_text = answer_dict
                sources = []
                query_type = "unknown"
            elif isinstance(answer_dict, dict):
                answer_text = answer_dict.get("answer", "No answer generated.")
                sources = answer_dict.get("sources", [])
                query_type = answer_dict.get("query_type", "unknown")
            else:
                answer_text = str(answer_dict) if answer_dict else "No answer generated."
                sources = []
                query_type = "unknown"
            
            return {
                "answer": answer_text,
                "session_id": request.session_id,
                "sources": sources,
                "query_type": query_type
            }
            
        except asyncio.TimeoutError:
            logger.error("[Chat] Request timed out after 60 seconds")
            raise HTTPException(
                status_code=504,
                detail="Request timed out. The question may be too complex or the document too large. Try a simpler question."
            )
        
    except ValidationError as e:
        logger.error(f"[Chat] Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"[Chat] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process question. Please try again."
        )


@router.delete("/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """
    Clear a chat session and its associated context.
    
    - **session_id**: The session ID to clear
    
    This is useful for freeing up memory/storage and starting fresh.
    """
    try:
        logger.info(f"[Chat] Clearing session: {session_id}")
        
        # Use persistent storage
        from core.rag_storage import get_rag_storage
        storage = get_rag_storage()
        
        deleted = storage.delete_rag_chain(session_id)
        
        if deleted:
            logger.info(f"[Chat]   Successfully deleted session: {session_id}")
            return {
                "message": f"Session {session_id} cleared successfully",
                "session_id": session_id,
                "deleted": True
            }
        else:
            logger.warning(f"[Chat] Session not found: {session_id}")
            return {
                "message": f"Session {session_id} not found",
                "session_id": session_id,
                "deleted": False
            }
        
    except Exception as e:
        logger.error(f"[Chat] Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")



@router.get("/chat/storage/health")
async def get_storage_health():
    """
    Get RAG storage health status.
    
    Returns information about:
    - Storage backend (Redis or in-memory)
    - Connection status
    - Number of stored sessions
    - Available session IDs
    """
    try:
        from core.rag_storage import get_rag_storage
        from main import list_all_rag_sessions
        
        storage = get_rag_storage()
        health = storage.health_check()
        
        # Add session list
        health['sessions'] = list_all_rag_sessions()
        
        return {
            "status": "healthy" if health['healthy'] else "degraded",
            "storage": health
        }
        
    except Exception as e:
        logger.error(f"[Chat] Storage health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
