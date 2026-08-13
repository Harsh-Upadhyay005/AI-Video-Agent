"""
FastAPI main application for AI Video Agent.
Production-ready API with proper error handling, logging, and monitoring.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional
import time
import uvicorn

from core.config import ConfigManager
from core.env_validator import validate_environment
from core.health_check import HealthCheck
from core.security import perform_security_check
from core.logger import get_logger
from core.exceptions import AIVideoAgentException
from core.resource_manager import cleanup_on_shutdown
from api.routes import analysis, health, chat

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 AI Video Agent API Starting...")
    logger.info("=" * 80)
    
    try:
        # Validate environment
        logger.info("Validating environment variables...")
        validate_environment(strict=True)
        
        # Initialize configuration
        logger.info("Initializing configuration...")
        config = ConfigManager.initialize()
        logger.info(f"Running in {config.environment} mode")
        
        # Run health checks
        logger.info("Running health checks...")
        health_results = HealthCheck.run_all_checks(skip_api_checks=False)
        
        if health_results["overall_status"] != "healthy":
            logger.warning("Health check warnings detected, but continuing startup")
        
        # Run security check
        logger.info("Running security check...")
        perform_security_check()
        
        logger.info("=" * 80)
        logger.info("[okay] AI Video Agent API Ready")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("[alert] AI Video Agent API Shutting Down...")
    logger.info("=" * 80)
    
    try:
        cleanup_on_shutdown()
        logger.info("[okay] Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="AI Video Agent API",
    description="Production-ready API for video/audio transcription, summarization, and RAG-based chat",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS Middleware - Configure based on your needs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing."""
    start_time = time.time()
    
    # Log request
    logger.info(f"→ {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"← {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"← {request.method} {request.url.path} "
            f"Error: {str(e)} "
            f"Duration: {process_time:.3f}s"
        )
        raise


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(AIVideoAgentException)
async def custom_exception_handler(request: Request, exc: AIVideoAgentException):
    """Handle custom application exceptions."""
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# =============================================================================
# Include Routers
# =============================================================================

# Include health routes both at root and /api/v1 for compatibility
app.include_router(health.router, tags=["Health"])  # /health (root level)
app.include_router(health.router, prefix="/api/v1", tags=["Health"])  # /api/v1/health
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Video Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info",
        access_log=True
    )
