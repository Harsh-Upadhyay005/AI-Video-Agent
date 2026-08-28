"""
Persistent RAG chain storage with Redis backend and in-memory fallback.

Architecture:
- Primary: Redis for production-grade persistence
- Fallback: In-memory dict if Redis unavailable
- Graceful degradation: System continues working without Redis

Usage:
    from core.rag_storage import get_rag_storage
    
    storage = get_rag_storage()
    storage.store_rag_chain("session_123", rag_chain)
    rag_chain = storage.get_rag_chain("session_123")
"""

import os
import pickle
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("[RAGStorage] Redis not available - using in-memory storage")


class RAGStorage:
    """
    Persistent RAG chain storage with Redis backend.
    
    Features:
    - Redis persistence with TTL (default 24 hours)
    - In-memory fallback if Redis unavailable
    - Graceful degradation (no crashes)
    - Session cleanup and TTL management
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 86400  # 24 hours in seconds
    ):
        """
        Initialize RAG storage.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            default_ttl: Default TTL for stored chains in seconds
        """
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None
        self._in_memory_store: Dict[str, Any] = {}
        self._using_redis = False
        
        # Try to connect to Redis
        if REDIS_AVAILABLE:
            redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False,  # We'll handle binary data (pickle)
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                self._using_redis = True
                logger.info(f"[RAGStorage] ✓ Connected to Redis: {redis_url}")
            except Exception as e:
                logger.warning(f"[RAGStorage] Redis connection failed: {e}")
                logger.warning("[RAGStorage] Falling back to in-memory storage")
                self.redis_client = None
        else:
            logger.info("[RAGStorage] Using in-memory storage (Redis not installed)")
    
    def store_rag_chain(
        self,
        session_id: str,
        rag_chain,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store RAG chain for a session.
        
        Args:
            session_id: Unique session identifier
            rag_chain: RAG chain instance to store
            ttl: Time-to-live in seconds (None = use default)
            
        Returns:
            True if stored successfully, False otherwise
        """
        ttl = ttl or self.default_ttl
        key = self._make_key(session_id)
        
        try:
            # Serialize RAG chain
            serialized = pickle.dumps(rag_chain)
            
            if self._using_redis and self.redis_client:
                # Store in Redis with TTL
                self.redis_client.setex(key, ttl, serialized)
                logger.info(f"[RAGStorage] ✓ Stored in Redis: {session_id} (TTL: {ttl}s)")
            else:
                # Store in memory (no TTL in fallback)
                self._in_memory_store[key] = serialized
                logger.info(f"[RAGStorage] ✓ Stored in memory: {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"[RAGStorage] Failed to store {session_id}: {e}")
            return False
    
    def get_rag_chain(self, session_id: str):
        """
        Retrieve RAG chain for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            RAG chain instance or None if not found
        """
        key = self._make_key(session_id)
        
        try:
            serialized = None
            
            if self._using_redis and self.redis_client:
                # Retrieve from Redis
                serialized = self.redis_client.get(key)
                if serialized:
                    logger.info(f"[RAGStorage] ✓ Retrieved from Redis: {session_id}")
            else:
                # Retrieve from memory
                serialized = self._in_memory_store.get(key)
                if serialized:
                    logger.info(f"[RAGStorage] ✓ Retrieved from memory: {session_id}")
            
            if serialized:
                return pickle.loads(serialized)
            
            logger.debug(f"[RAGStorage] Not found: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"[RAGStorage] Failed to retrieve {session_id}: {e}")
            return None
    
    def delete_rag_chain(self, session_id: str) -> bool:
        """
        Delete RAG chain for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False otherwise
        """
        key = self._make_key(session_id)
        
        try:
            if self._using_redis and self.redis_client:
                deleted = self.redis_client.delete(key)
                logger.info(f"[RAGStorage] Deleted from Redis: {session_id}")
                return deleted > 0
            else:
                if key in self._in_memory_store:
                    del self._in_memory_store[key]
                    logger.info(f"[RAGStorage] Deleted from memory: {session_id}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"[RAGStorage] Failed to delete {session_id}: {e}")
            return False
    
    def list_sessions(self) -> list:
        """
        List all stored session IDs.
        
        Returns:
            List of session IDs
        """
        try:
            if self._using_redis and self.redis_client:
                # Get all keys matching pattern
                pattern = self._make_key("*")
                keys = self.redis_client.keys(pattern)
                session_ids = [key.decode('utf-8').replace('rag_chain:', '') for key in keys]
                logger.debug(f"[RAGStorage] Found {len(session_ids)} sessions in Redis")
                return session_ids
            else:
                # Get from memory
                prefix = "rag_chain:"
                session_ids = [
                    key.replace(prefix, '')
                    for key in self._in_memory_store.keys()
                    if key.startswith(prefix)
                ]
                logger.debug(f"[RAGStorage] Found {len(session_ids)} sessions in memory")
                return session_ids
                
        except Exception as e:
            logger.error(f"[RAGStorage] Failed to list sessions: {e}")
            return []
    
    def get_most_recent_session(self) -> Optional[str]:
        """
        Get the most recently stored session ID.
        
        Note: This is approximate in Redis (no timestamps stored).
        In memory, returns last inserted.
        
        Returns:
            Session ID or None
        """
        sessions = self.list_sessions()
        if sessions:
            # Return last session (most recent in insertion order)
            return sessions[-1]
        return None
    
    def clear_all(self) -> int:
        """
        Clear all stored RAG chains.
        
        WARNING: Use with caution!
        
        Returns:
            Number of sessions cleared
        """
        try:
            if self._using_redis and self.redis_client:
                pattern = self._make_key("*")
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    logger.info(f"[RAGStorage] Cleared {deleted} sessions from Redis")
                    return deleted
                return 0
            else:
                count = len([k for k in self._in_memory_store.keys() if k.startswith('rag_chain:')])
                self._in_memory_store = {
                    k: v for k, v in self._in_memory_store.items()
                    if not k.startswith('rag_chain:')
                }
                logger.info(f"[RAGStorage] Cleared {count} sessions from memory")
                return count
                
        except Exception as e:
            logger.error(f"[RAGStorage] Failed to clear: {e}")
            return 0
    
    def is_using_redis(self) -> bool:
        """Check if storage is using Redis backend."""
        return self._using_redis
    
    def _make_key(self, session_id: str) -> str:
        """Create Redis key from session ID."""
        return f"rag_chain:{session_id}"
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check storage health.
        
        Returns:
            Health status dictionary
        """
        status = {
            'using_redis': self._using_redis,
            'redis_available': REDIS_AVAILABLE,
            'storage_type': 'redis' if self._using_redis else 'memory',
            'session_count': len(self.list_sessions()),
            'healthy': True
        }
        
        if self._using_redis and self.redis_client:
            try:
                self.redis_client.ping()
                status['redis_connected'] = True
            except Exception as e:
                status['redis_connected'] = False
                status['redis_error'] = str(e)
                status['healthy'] = False
        
        return status


# Singleton instance
_rag_storage_instance: Optional[RAGStorage] = None


def get_rag_storage() -> RAGStorage:
    """
    Get singleton RAG storage instance.
    
    Returns:
        RAGStorage instance
    """
    global _rag_storage_instance
    
    if _rag_storage_instance is None:
        _rag_storage_instance = RAGStorage()
    
    return _rag_storage_instance


def reset_rag_storage():
    """Reset singleton (useful for testing)."""
    global _rag_storage_instance
    _rag_storage_instance = None
