"""
Health check endpoints for monitoring and diagnostics.
"""

from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from core.health_check import HealthCheck
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    checks: Dict[str, Any]


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Video Agent API"
    }


@router.get("/health/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    Detailed health check with all system components.
    Useful for monitoring and diagnostics.
    """
    logger.info("Running detailed health check...")
    
    # Run all health checks
    results = HealthCheck.run_all_checks(skip_api_checks=False)
    
    return {
        "status": results["overall_status"],
        "timestamp": results["timestamp"],
        "checks": results["checks"]
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if service is ready to accept traffic.
    """
    try:
        # Quick check of critical components
        results = HealthCheck.run_all_checks(skip_api_checks=True)
        
        if results["overall_status"] == "healthy":
            return {"status": "ready"}
        else:
            return Response(status_code=503, content="Service not ready")
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return Response(status_code=503, content="Service not ready")


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if service is alive (even if temporarily unavailable).
    """
    return {"status": "alive"}
