"""User account export endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/account/export")
async def export_account_data():
    """Export analysis session IDs stored on this server (no secrets)."""
    try:
        from main import list_all_rag_sessions

        sessions = list_all_rag_sessions() or []
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "session_ids": sessions,
            "session_count": len(sessions),
        }
    except Exception as e:
        logger.error(f"[Account] Export failed: {e}", exc_info=True)
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "session_ids": [],
            "session_count": 0,
            "warning": "Could not list server sessions",
        }
