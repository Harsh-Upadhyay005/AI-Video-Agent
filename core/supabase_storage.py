"""
Supabase Storage Manager for File Upload/Download.
Handles media file storage in Supabase Storage buckets.
"""

import os
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime

from core.supabase_client import get_supabase_client
from core.logger import get_logger

logger = get_logger(__name__)


class SupabaseStorageManager:
    """
    Manages file operations with Supabase Storage.
    Handles upload, download, delete, and URL generation.
    """
    
    def __init__(self, bucket_name: str = "media-files"):
        """
        Initialize storage manager.
        
        Args:
            bucket_name: Name of the Supabase storage bucket
        """
        self.bucket_name = bucket_name
        self.client = get_supabase_client()
        
        if not self.client.is_available:
            logger.warning("Supabase not configured. Storage operations will fail.")
    
    def upload_file(
        self,
        file_path: str,
        storage_path: str,
        file_obj: Optional[BinaryIO] = None
    ) -> dict:
        """
        Upload file to Supabase Storage.
        
        Args:
            file_path: Local file path (if file_obj not provided)
            storage_path: Destination path in Supabase (e.g., "uploads/job_123/file.mp3")
            file_obj: Optional file object (if provided, file_path is ignored)
            
        Returns:
            Dictionary with upload result:
                - success: bool
                - storage_path: str
                - public_url: str
                - error: str (if failed)
        """
        if not self.client.is_available:
            return {
                "success": False,
                "error": "Supabase not configured"
            }
        
        try:
            # Read file data
            if file_obj:
                file_data = file_obj.read()
                file_name = storage_path.split('/')[-1]
            else:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                file_name = os.path.basename(file_path)
            
            # Get content type
            content_type = self._get_content_type(file_name)
            
            logger.info(f"Uploading to Supabase: {storage_path} ({len(file_data)} bytes)")
            
            # Upload to Supabase Storage
            storage = self.client.get_storage()
            response = storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            public_url = storage.from_(self.bucket_name).get_public_url(storage_path)
            
            logger.info(f"Upload successful: {public_url}")
            
            return {
                "success": True,
                "storage_path": storage_path,
                "public_url": public_url,
                "bucket": self.bucket_name
            }
            
        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def download_file(
        self,
        storage_path: str,
        local_path: str
    ) -> bool:
        """
        Download file from Supabase Storage to local path.
        
        Args:
            storage_path: Path in Supabase storage
            local_path: Destination local file path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client.is_available:
            logger.error("Supabase not configured")
            return False
        
        try:
            logger.info(f"Downloading from Supabase: {storage_path}")
            
            # Download from Supabase
            storage = self.client.get_storage()
            file_data = storage.from_(self.bucket_name).download(storage_path)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Download successful: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from Supabase Storage.
        
        Args:
            storage_path: Path in Supabase storage
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client.is_available:
            logger.error("Supabase not configured")
            return False
        
        try:
            logger.info(f"Deleting from Supabase: {storage_path}")
            
            storage = self.client.get_storage()
            storage.from_(self.bucket_name).remove([storage_path])
            
            logger.info(f"Delete successful: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_public_url(self, storage_path: str) -> Optional[str]:
        """
        Get public URL for a file in storage.
        
        Args:
            storage_path: Path in Supabase storage
            
        Returns:
            Public URL or None if failed
        """
        if not self.client.is_available:
            return None
        
        try:
            storage = self.client.get_storage()
            url = storage.from_(self.bucket_name).get_public_url(storage_path)
            return url
        except Exception as e:
            logger.error(f"Failed to get public URL: {e}")
            return None
    
    def file_exists(self, storage_path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            storage_path: Path in Supabase storage
            
        Returns:
            True if exists, False otherwise
        """
        if not self.client.is_available:
            return False
        
        try:
            storage = self.client.get_storage()
            files = storage.from_(self.bucket_name).list(
                path=os.path.dirname(storage_path)
            )
            
            file_name = os.path.basename(storage_path)
            return any(f['name'] == file_name for f in files)
            
        except Exception as e:
            logger.error(f"Failed to check file existence: {e}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get content type based on file extension.
        
        Args:
            filename: File name with extension
            
        Returns:
            MIME type string
        """
        ext = Path(filename).suffix.lower()
        
        content_types = {
            # Audio
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.aac': 'audio/aac',
            # Video
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            # Documents
            '.pdf': 'application/pdf',
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def generate_storage_path(
        self,
        job_id: str,
        filename: str,
        subfolder: str = "uploads"
    ) -> str:
        """
        Generate organized storage path.
        
        Args:
            job_id: Unique job identifier
            filename: Original filename
            subfolder: Optional subfolder (default: "uploads")
            
        Returns:
            Storage path string (e.g., "uploads/2024-01/job_abc123/file.mp3")
        """
        # Organize by year-month for better structure
        date_folder = datetime.now().strftime("%Y-%m")
        
        # Clean filename (remove special characters)
        safe_filename = "".join(
            c for c in filename if c.isalnum() or c in ('_', '-', '.')
        )
        
        storage_path = f"{subfolder}/{date_folder}/job_{job_id}/{safe_filename}"
        return storage_path


# Global instance
_storage_manager: Optional[SupabaseStorageManager] = None


def get_storage_manager() -> SupabaseStorageManager:
    """
    Get singleton storage manager instance.
    
    Returns:
        SupabaseStorageManager instance
    """
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = SupabaseStorageManager()
    return _storage_manager
