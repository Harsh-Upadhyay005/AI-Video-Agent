"""
Video/Audio analysis endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from enum import Enum
import asyncio
import json
import uuid

from core.validators import InputValidator
from core.logger import get_logger
from core.exceptions import ValidationError
from main import run_pipeline, get_rag_chain_for_source
from utils.file_manager import get_file_manager

logger = get_logger(__name__)

router = APIRouter()

# Store for progress updates (in production, use Redis or database)
progress_store = {}


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
    Analyze a video or audio file asynchronously with real-time progress.
    
    - **source**: YouTube URL or local file path
    - **language**: Language for transcription (english or hinglish)
    
    Returns a job ID. Use /progress/{job_id} to get real-time progress updates.
    """
    try:
        # Validate source input
        validated_source, source_type = InputValidator.validate_source_input(request.source)
        language = InputValidator.validate_language(request.language.value)
        
        logger.info(f"Starting analysis: source_type={source_type}, language={language}")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize progress
        progress_store[job_id] = {
            "status": "starting",
            "stage": "initialization",
            "progress": 0,
            "message": "Starting analysis...",
            "result": None,
            "error": None
        }
        
        # Start processing in background
        background_tasks.add_task(process_analysis_with_progress, job_id, validated_source, language)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": f"Analysis started. Stream progress at /progress/{job_id}"
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start analysis")


async def process_analysis_with_progress(job_id: str, source: str, language: str):
    """
    Process the analysis with real-time progress updates.
    
    Args:
        job_id: Unique job identifier
        source: Validated source path/URL
        language: Validated language
    """
    def update_progress(stage: str, message: str, progress: int = None):
        """Update progress in store."""
        if job_id in progress_store:
            progress_store[job_id].update({
                "stage": stage,
                "message": message,
                "status": "processing"
            })
            if progress is not None:
                progress_store[job_id]["progress"] = progress
    
    try:
        logger.info(f"Processing job {job_id}: source={source}, language={language}")
        
        update_progress("downloading", "Downloading audio from URL...", 10)
        
        # Run the pipeline with progress callback
        # Note: Pipeline internally stores RAG chain using the source_key parameter
        result = run_pipeline(source, language, progress_callback=update_progress, source_key=job_id)
        
        # Ensure result contains only JSON-serializable data
        # Filter out any non-serializable objects (defense in depth)
        json_safe_result = {
            "title": result.get("title", ""),
            "transcript": result.get("transcript", ""),
            "summary": result.get("summary", ""),
            "action_items": result.get("action_items", ""),
            "key_decisions": result.get("key_decisions", ""),
            "open_questions": result.get("open_questions", ""),
            "job_id": job_id  # Include job_id so frontend can use it for chat
        }
        
        # Store result (guaranteed JSON-serializable)
        progress_store[job_id].update({
            "status": "completed",
            "stage": "done",
            "progress": 100,
            "message": "Analysis complete!",
            "result": json_safe_result
        })
        
        logger.info(f"Job {job_id} completed successfully")
        
    except ValueError as e:
        # Handle empty transcript or validation errors
        logger.error(f"Job {job_id} validation failed: {str(e)}", exc_info=True)
        progress_store[job_id].update({
            "status": "failed",
            "stage": "error",
            "progress": 0,
            "message": str(e),
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        progress_store[job_id].update({
            "status": "failed",
            "stage": "error",
            "message": str(e),
            "error": str(e)
        })


@router.get("/progress/{job_id}")
async def stream_progress(job_id: str):
    """
    Stream real-time progress updates for an analysis job using Server-Sent Events (SSE).
    
    - **job_id**: The job ID returned from /analyze endpoint
    
    Returns a stream of progress updates.
    """
    async def event_generator():
        """Generate SSE events."""
        if job_id not in progress_store:
            yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            return
        
        last_progress = -1
        
        while True:
            if job_id not in progress_store:
                break
            
            progress_data = progress_store[job_id]
            current_progress = progress_data.get("progress", 0)
            
            # Send update if progress changed or status is completed/failed
            if current_progress != last_progress or progress_data["status"] in ["completed", "failed"]:
                # progress_data contains only JSON-serializable fields:
                # - status (str)
                # - stage (str)
                # - progress (int)
                # - message (str)
                # - result (dict with strings only, no LangChain objects)
                # - error (str or None)
                yield f"data: {json.dumps(progress_data)}\n\n"
                last_progress = current_progress
            
            # Stop streaming if completed or failed
            if progress_data["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(0.5)  # Poll every 500ms
        
        # Clean up after completion
        if job_id in progress_store and progress_store[job_id]["status"] in ["completed", "failed"]:
            await asyncio.sleep(5)  # Keep result for 5 seconds
            progress_store.pop(job_id, None)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


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
    Only use for turbo files or testing. Use /analyze for production.
    
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


@router.post("/upload", response_model=AnalysisResponse)
async def upload_and_analyze(
    file: UploadFile = File(..., description="Audio or video file (MP3, MP4, etc.)"),
    language: str = Form(default="english", description="Language for transcription"),
    background_tasks: BackgroundTasks = None
):
    """
    Upload an audio/video file and analyze it asynchronously.
    
    Supported formats:
    - Audio: MP3, WAV, M4A, FLAC, OGG, AAC
    - Video: MP4, AVI, MOV, MKV, WebM, FLV
    
    - **file**: Audio or video file to analyze
    - **language**: Language for transcription (english or hinglish)
    
    Returns a job ID. Use /progress/{job_id} to get real-time progress updates.
    
    Maximum file size: Configured via MAX_UPLOAD_SIZE_MB environment variable (default: 500MB)
    """
    try:
        # Validate language
        validated_language = InputValidator.validate_language(language)
        
        logger.info(f"Processing file upload: {file.filename}, language={validated_language}")
        
        # Get file manager
        file_manager = get_file_manager()
        
        # Save and validate uploaded file (with Supabase integration)
        job_id, file_path, file_size, supabase_info = await file_manager.save_upload(
            file=file,
            language=validated_language,
            upload_to_supabase=True  # Enable Supabase upload
        )
        
        logger.info(
            f"File uploaded successfully: job_id={job_id}, "
            f"path={file_path}, size={file_size / (1024 * 1024):.2f}MB, "
            f"supabase={supabase_info.get('uploaded', False)}"
        )
        
        # Initialize progress
        progress_store[job_id] = {
            "status": "starting",
            "stage": "upload_complete",
            "progress": 5,
            "message": "File uploaded successfully",
            "result": None,
            "error": None
        }
        
        # Start processing in background
        background_tasks.add_task(
            process_uploaded_file_with_progress,
            job_id,
            file_path,
            validated_language,
            file_manager
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": f"Upload successful. Processing started. Stream progress at /progress/{job_id}"
        }
        
    except ValidationError as e:
        logger.error(f"Upload validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process upload")


async def process_uploaded_file_with_progress(
    job_id: str,
    file_path: str,
    language: str,
    file_manager
):
    """
    Process uploaded file with real-time progress updates.
    
    Args:
        job_id: Unique job identifier
        file_path: Path to uploaded file
        language: Validated language
        file_manager: FileManager instance for cleanup
    """
    def update_progress(stage: str, message: str, progress: int = None):
        """Update progress in store."""
        if job_id in progress_store:
            progress_store[job_id].update({
                "stage": stage,
                "message": message,
                "status": "processing"
            })
            if progress is not None:
                progress_store[job_id]["progress"] = progress
    
    try:
        logger.info(f"Processing uploaded file job {job_id}: file={file_path}, language={language}")
        
        update_progress("processing", "Processing uploaded file...", 10)
        
        # Run the pipeline with the uploaded file path
        # The audio_processor will handle conversion and chunking
        result = run_pipeline(file_path, language, progress_callback=update_progress, source_key=job_id)
        
        # Ensure result contains only JSON-serializable data
        json_safe_result = {
            "title": result.get("title", ""),
            "transcript": result.get("transcript", ""),
            "summary": result.get("summary", ""),
            "action_items": result.get("action_items", ""),
            "key_decisions": result.get("key_decisions", ""),
            "open_questions": result.get("open_questions", ""),
            "job_id": job_id
        }
        
        # Store result
        progress_store[job_id].update({
            "status": "completed",
            "stage": "done",
            "progress": 100,
            "message": "Analysis complete!",
            "result": json_safe_result
        })
        
        logger.info(f"Job {job_id} completed successfully")
        
        # Save results to Supabase if configured
        try:
            from core.supabase_database import get_database_manager
            from core.supabase_client import is_supabase_configured
            
            if is_supabase_configured():
                logger.info(f"Saving results to Supabase: {job_id}")
                db_manager = get_database_manager()
                db_manager.save_processing_result(job_id, json_safe_result)
        except Exception as e:
            logger.warning(f"Failed to save results to Supabase: {e}")
        
        # Clean up uploaded file after successful processing
        file_manager.cleanup_job(job_id)
        
    except ValueError as e:
        logger.error(f"Job {job_id} validation failed: {str(e)}", exc_info=True)
        progress_store[job_id].update({
            "status": "failed",
            "stage": "error",
            "progress": 0,
            "message": str(e),
            "error": str(e)
        })
        # Clean up on error
        file_manager.cleanup_job(job_id)
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        progress_store[job_id].update({
            "status": "failed",
            "stage": "error",
            "message": str(e),
            "error": str(e)
        })
        # Clean up on error
        file_manager.cleanup_job(job_id)


