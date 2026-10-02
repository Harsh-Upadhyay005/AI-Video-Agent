"""
Chat Memory Service — Persist conversation history per user + session.

Stores messages in Supabase `chat_history` table when available,
with an in-memory fallback for local development without Supabase.

Table schema (create in Supabase SQL Editor):
    CREATE TABLE IF NOT EXISTS chat_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_chat_history_user_session
        ON chat_history(user_id, session_id, created_at);
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from core.logger import get_logger

logger = get_logger(__name__)


class ChatMemoryService:
    """
    Persist and retrieve chat messages per user + session.
    Uses Supabase when configured, falls back to in-memory dict.
    """

    TABLE = "chat_history"

    def __init__(self):
        self._supabase = None
        self._memory: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        self._init_supabase()

    def _init_supabase(self):
        """Try to connect to Supabase for persistence."""
        try:
            from core.supabase_client import get_supabase_client
            client = get_supabase_client()
            if client.is_available:
                self._supabase = client.get_database()
                logger.info("[ChatMemory] Supabase persistence enabled")
            else:
                logger.info("[ChatMemory] Supabase not available — using in-memory storage")
        except Exception as e:
            logger.warning(f"[ChatMemory] Supabase init failed ({e}) — using in-memory storage")

    # ------------------------------------------------------------------ #
    # Save
    # ------------------------------------------------------------------ #
    def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> bool:
        """
        Persist a single chat message.

        Args:
            user_id:    Authenticated user ID (or 'guest')
            session_id: Analysis job / session ID
            role:       'user' or 'assistant'
            content:    Message text

        Returns:
            True on success
        """
        now = datetime.utcnow().isoformat()
        record = {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": now,
        }

        # In-memory (always, as fast cache)
        self._memory[user_id][session_id].append(record)

        # Supabase (if available)
        if self._supabase:
            try:
                self._supabase.table(self.TABLE).insert(record).execute()
            except Exception as e:
                logger.warning(f"[ChatMemory] Supabase insert failed: {e}")
                return False

        return True

    # ------------------------------------------------------------------ #
    # Load
    # ------------------------------------------------------------------ #
    def get_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a user + session, ordered chronologically.

        Returns list of {role, content, created_at}.
        """
        # Try Supabase first
        if self._supabase:
            try:
                resp = (
                    self._supabase.table(self.TABLE)
                    .select("role, content, created_at")
                    .eq("user_id", user_id)
                    .eq("session_id", session_id)
                    .order("created_at", desc=False)
                    .limit(limit)
                    .execute()
                )
                if resp.data:
                    return resp.data
            except Exception as e:
                logger.warning(f"[ChatMemory] Supabase select failed: {e}")

        # Fallback: in-memory
        return self._memory.get(user_id, {}).get(session_id, [])[-limit:]

    # ------------------------------------------------------------------ #
    # List sessions
    # ------------------------------------------------------------------ #
    def list_sessions(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List sessions with their latest message for a user.

        Returns list of {session_id, last_message, last_role, updated_at}.
        """
        if self._supabase:
            try:
                # Get distinct sessions with latest message using RPC or sub-query
                # For simplicity, fetch recent messages and deduplicate in Python
                resp = (
                    self._supabase.table(self.TABLE)
                    .select("session_id, role, content, created_at")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(500)  # Fetch enough to cover many sessions
                    .execute()
                )
                if resp.data:
                    seen = {}
                    for row in resp.data:
                        sid = row["session_id"]
                        if sid not in seen:
                            seen[sid] = {
                                "session_id": sid,
                                "last_message": (row["content"] or "")[:120],
                                "last_role": row["role"],
                                "updated_at": row["created_at"],
                            }
                    sessions = list(seen.values())[:limit]
                    return sessions
            except Exception as e:
                logger.warning(f"[ChatMemory] Supabase list_sessions failed: {e}")

        # Fallback: in-memory
        sessions = []
        for sid, msgs in self._memory.get(user_id, {}).items():
            if msgs:
                last = msgs[-1]
                sessions.append({
                    "session_id": sid,
                    "last_message": (last.get("content") or "")[:120],
                    "last_role": last.get("role", ""),
                    "updated_at": last.get("created_at", ""),
                })
        sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
        return sessions[:limit]

    # ------------------------------------------------------------------ #
    # Clear
    # ------------------------------------------------------------------ #
    def clear_session(self, user_id: str, session_id: str) -> bool:
        """Delete all messages for a user + session."""
        # In-memory
        if user_id in self._memory and session_id in self._memory[user_id]:
            del self._memory[user_id][session_id]

        # Supabase
        if self._supabase:
            try:
                (
                    self._supabase.table(self.TABLE)
                    .delete()
                    .eq("user_id", user_id)
                    .eq("session_id", session_id)
                    .execute()
                )
            except Exception as e:
                logger.warning(f"[ChatMemory] Supabase delete failed: {e}")
                return False

        return True


# Singleton
_chat_memory_instance: Optional[ChatMemoryService] = None


def get_chat_memory() -> ChatMemoryService:
    """Get singleton ChatMemoryService instance."""
    global _chat_memory_instance
    if _chat_memory_instance is None:
        _chat_memory_instance = ChatMemoryService()
    return _chat_memory_instance
