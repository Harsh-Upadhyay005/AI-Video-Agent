"""
Video/Audio analysis endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from enum import Enum

from core.validators import InputValidator
from core.logger import get_logger
from core.exceptions import ValidationError
from main import run_pipeline

logger = get_logger(__name__)

router = APIRouter()


class LanguageEnum(str, Enum):
    """Supported languages."""
    english = "english"
    hinglish = "hinglish"


class AnalysisRequest(BaseModel):
    """Request model for video/audio analysis."""
    source: str = Field(..., description="YouTube URL or local file path", min_length=1)
    language: LanguageEnum = Field(default=LanguageEnum.english, description="Language for transcription")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "english"
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for video/audio analysis."""
    job_id: str
    status: str
    message: str


class AnalysisResult(BaseModel):
    """Analysis result model."""
    title: str
    transcript: str
    summary: str
    action_items: str
    key_decisions: str
    open_questions: str


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a video or audio file.
    
    - **source**: YouTube URL or local file path
    - **language**: Language for transcription (english or hinglish)
    
    Returns a job ID for tracking the analysis progress.
    """
    try:
        # Validate source input
        validated_source, source_type = InputValidator.validate_source_input(request.source)
        language = InputValidator.validate_language(request.language.value)
        
        logger.info(f"Starting analysis: source_type={source_type}, language={language}")
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # In a production system, you would:
        # 1. Store the job in a database
        # 2. Use a task queue (Celery, RQ, etc.)
        # 3. Return the job ID immediately
        # 4. Process asynchronously
        
        # For now, we'll process synchronously but return immediately
        background_tasks.add_task(process_analysis, job_id, validated_source, language)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Analysis started. Use /status/{job_id} to check progress."
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start analysis")


async def process_analysis(job_id: str, source: str, language: str):
    """
    Process the analysis in the background.
    
    Args:
        job_id: Unique job identifier
        source: Validated source path/URL
        language: Validated language
    """
    try:
        logger.info(f"Processing job {job_id}: source={source}, language={language}")
        
        # Run the pipeline
        result = run_pipeline(source, language)
        
        # In production: Store result in database/cache with job_id
        logger.info(f"Job {job_id} completed successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        # In production: Update job status in database
        raise


@router.get("/status/{job_id}")
async def get_analysis_status(job_id: str):
    """
    Get the status of an analysis job.
    
    - **job_id**: The job ID returned from /analyze endpoint
    
    Returns the current status and result (if completed).
    """
    # In production: Query database/cache for job status
    # For now, return a placeholder
    
    return {
        "job_id": job_id,
        "status": "completed",  # or "processing", "failed"
        "message": "This is a placeholder. Implement persistent storage for production."
    }


@router.post("/analyze/sync", response_model=AnalysisResult)
async def analyze_video_sync(request: AnalysisRequest):
    """
    Synchronously analyze a video or audio file.
    
    ⚠️ WARNING: This endpoint blocks until analysis is complete.
    Only use for small files or testing. Use /analyze for production.
    
    - **source**: YouTube URL or local file path
    - **language**: Language for transcription (english or hinglish)
    
    Returns the complete analysis result.
    """
    try:
        # Validate source input
        validated_source, source_type = InputValidator.validate_source_input(request.source)
        language = InputValidator.validate_language(request.language.value)
        
        logger.info(f"Starting synchronous analysis: source_type={source_type}, language={language}")
        
        # Run the pipeline
        result = run_pipeline(validated_source, language)
        
        return {
            "title": result["title"],
            "transcript": result["transcript"],
            "summary": result["summary"],
            "action_items": result["action_items"],
            "key_decisions": result["key_decisions"],
            "open_questions": result["open_questions"]
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed")
