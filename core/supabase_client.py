"""
Supabase Client Configuration and Initialization.
Provides centralized Supabase client for storage and database operations.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("[Supabase] Warning: supabase-py not installed. Supabase features disabled.")


class SupabaseClient:
    """
    Singleton Supabase client manager.
    Provides access to Supabase storage and database.
    """
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client (only once)."""
        if not self._initialized:
            self._initialize_client()
            self._initialized = True
    
    def _initialize_client(self):
        """Initialize Supabase client with credentials from environment."""
        if not SUPABASE_AVAILABLE:
            print("[Supabase] Supabase SDK not available. Install with: pip install supabase")
            return
        
        # Get credentials from environment
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("[Supabase] Warning: SUPABASE_URL or SUPABASE_ANON_KEY not set in .env")
            print("[Supabase] Supabase features will be disabled")
            return
        
        try:
            self._client = create_client(supabase_url, supabase_key)
            print(f"[Supabase] Client initialized successfully: {supabase_url}")
        except Exception as e:
            print(f"[Supabase] Failed to initialize client: {e}")
            self._client = None
    
    @property
    def client(self) -> Optional[Client]:
        """Get Supabase client instance."""
        return self._client
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase client is available and configured."""
        return self._client is not None
    
    def get_storage(self):
        """Get Supabase storage client."""
        if not self.is_available:
            raise RuntimeError("Supabase client not available")
        return self._client.storage
    
    def get_database(self):
        """Get Supabase database client."""
        if not self.is_available:
            raise RuntimeError("Supabase client not available")
        return self._client


# Global instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Get singleton Supabase client instance.
    
    Returns:
        SupabaseClient instance
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


def is_supabase_configured() -> bool:
    """
    Check if Supabase is configured and available.
    
    Returns:
        True if Supabase is configured, False otherwise
    """
    client = get_supabase_client()
    return client.is_available
