"""
Secure file upload manager for handling multipart file uploads.
Provides validation, temporary storage, cleanup, and Supabase integration.
"""

import os
import uuid
import shutil
import magic
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from core.logger import get_logger
from core.exceptions import ValidationError

# Supabase integration (optional)
try:
    from core.supabase_storage import get_storage_manager
    from core.supabase_database import get_database_manager
    from core.supabase_client import is_supabase_configured
    SUPABASE_INTEGRATION = True
except ImportError:
    SUPABASE_INTEGRATION = False

logger = get_logger(__name__)


class FileManager:
    """Manages uploaded file operations with security and cleanup."""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac',
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv',
        '.pdf'
    }
    
    # MIME type validation (mapping for common formats)
    ALLOWED_MIME_TYPES = {
        # Audio
        'audio/mpeg': ['.mp3'],
        'audio/wav': ['.wav'],
        'audio/x-wav': ['.wav'],
        'audio/wave': ['.wav'],
        'audio/mp4': ['.m4a'],
        'audio/x-m4a': ['.m4a'],
        'audio/flac': ['.flac'],
        'audio/ogg': ['.ogg'],
        'audio/aac': ['.aac'],
        # Video
        'video/mp4': ['.mp4'],
        'video/x-msvideo': ['.avi'],
        'video/quicktime': ['.mov'],
        'video/x-matroska': ['.mkv'],
        'video/webm': ['.webm'],
        'video/x-flv': ['.flv'],
        # Documents
        'application/pdf': ['.pdf'],
    }
    
    def __init__(self, temp_dir: str = "temp", max_size_mb: int = 500):
        """
        Initialize file manager.
        
        Args:
            temp_dir: Directory for temporary file storage
            max_size_mb: Maximum file size in MB
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        logger.info(f"FileManager initialized: temp_dir={self.temp_dir}, max_size={max_size_mb}MB")
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        return str(uuid.uuid4())
    
    def _get_job_dir(self, job_id: str) -> Path:
        """Get directory for a specific job."""
        job_dir = self.temp_dir / f"job_{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir
    
    def _validate_extension(self, filename: str) -> str:
        """
        Validate file extension.
        
        Args:
            filename: Original filename
            
        Returns:
            Lowercase extension
            
        Raises:
            ValidationError: If extension not allowed
        """
        ext = Path(filename).suffix.lower()
        
        if not ext:
            raise ValidationError("File has no extension")
        
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file format: {ext}. "
                f"Supported formats: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )
        
        return ext
    
    def _validate_mime_type(self, file_path: Path, expected_ext: str) -> bool:
        """
        Validate MIME type matches file extension.
        
        Args:
            file_path: Path to uploaded file
            expected_ext: Expected extension (e.g., '.mp3')
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If MIME type doesn't match
        """
        try:
            # Use python-magic to detect actual file type
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(str(file_path))
            
            # Check if detected MIME type is in our allowed list
            if detected_mime not in self.ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f"Invalid file content. Detected type: {detected_mime} "
                    f"is not a supported media format."
                )
            
            # Check if extension matches MIME type
            allowed_exts = self.ALLOWED_MIME_TYPES[detected_mime]
            if expected_ext not in allowed_exts:
                raise ValidationError(
                    f"File extension {expected_ext} doesn't match detected content type: {detected_mime}. "
                    f"File may be corrupted or incorrectly named."
                )
            
            logger.info(f"MIME validation passed: {detected_mime} matches {expected_ext}")
            return True
            
        except ImportError:
            # python-magic not installed - skip MIME validation but log warning
            logger.warning("python-magic not installed - skipping MIME type validation")
            return True
        except Exception as e:
            logger.error(f"MIME type validation failed: {e}")
            raise ValidationError(f"Could not validate file content: {str(e)}")
    
    def _validate_file_size(self, file: UploadFile) -> int:
        """
        Validate file size.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            File size in bytes
            
        Raises:
            ValidationError: If file too large or empty
        """
        # Try to get size from content-length header first
        file_size = None
        
        # Read file to check actual size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size == 0:
            raise ValidationError("Uploaded file is empty")
        
        if file_size > self.max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise ValidationError(
                f"File too large: {size_mb:.1f}MB. Maximum allowed: {max_mb}MB"
            )
        
        logger.info(f"File size validation passed: {file_size / (1024 * 1024):.2f}MB")
        return file_size
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name
        
        # Remove dangerous characters
        import re
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename
    
    async def save_upload(self, file: UploadFile, language: str = "english", upload_to_supabase: bool = True) -> Tuple[str, str, int, dict]:
        """
        Save uploaded file to temporary storage with validation and optional Supabase upload.
        
        Args:
            file: FastAPI UploadFile object
            language: Language for transcription
            upload_to_supabase: Whether to upload to Supabase Storage (default: True)
            
        Returns:
            Tuple of (job_id, file_path, file_size, supabase_info)
            
        Raises:
            ValidationError: If file validation fails
        """
        try:
            logger.info(f"Processing upload: {file.filename}")
            
            # Validate extension
            ext = self._validate_extension(file.filename)
            
            # Validate file size
            file_size = self._validate_file_size(file)
            
            # Generate job ID and create directory
            job_id = self._generate_job_id()
            job_dir = self._get_job_dir(job_id)
            
            # Create safe filename
            safe_name = self._sanitize_filename(file.filename)
            file_path = job_dir / safe_name
            
            # Save file
            logger.info(f"Saving file to: {file_path}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Validate MIME type after saving
            self._validate_mime_type(file_path, ext)
            
            # Verify file was saved correctly
            if not file_path.exists():
                raise ValidationError("Failed to save file")
            
            saved_size = file_path.stat().st_size
            if saved_size != file_size:
                raise ValidationError(
                    f"File size mismatch after save: expected {file_size}, got {saved_size}"
                )
            
            logger.info(
                f"Upload successful: job_id={job_id}, "
                f"file={safe_name}, size={file_size / (1024 * 1024):.2f}MB"
            )
            
            # Upload to Supabase if enabled and configured
            supabase_info = {"uploaded": False}
            
            if upload_to_supabase and SUPABASE_INTEGRATION and is_supabase_configured():
                try:
                    logger.info(f"Uploading to Supabase Storage: {job_id}")
                    
                    storage_manager = get_storage_manager()
                    db_manager = get_database_manager()
                    
                    # Generate storage path
                    storage_path = storage_manager.generate_storage_path(job_id, safe_name)
                    
                    # Upload file
                    upload_result = storage_manager.upload_file(
                        file_path=str(file_path),
                        storage_path=storage_path
                    )
                    
                    if upload_result["success"]:
                        logger.info(f"Supabase upload successful: {upload_result['public_url']}")
                        
                        supabase_info = {
                            "uploaded": True,
                            "storage_path": storage_path,
                            "public_url": upload_result["public_url"],
                            "bucket": upload_result["bucket"]
                        }
                        
                        # Save metadata to Supabase database
                        db_manager.save_file_metadata({
                            "job_id": job_id,
                            "file_name": safe_name,
                            "file_type": ext,
                            "file_size": file_size,
                            "storage_path": storage_path,
                            "language": language,
                            "status": "processing"
                        })
                    else:
                        logger.warning(f"Supabase upload failed: {upload_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Supabase upload error: {e}")
                    # Continue with local processing even if Supabase fails
            
            return job_id, str(file_path), file_size, supabase_info
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to process upload: {str(e)}")
    
    def cleanup_job(self, job_id: str) -> bool:
        """
        Clean up all files for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cleanup successful
        """
        try:
            job_dir = self.temp_dir / f"job_{job_id}"
            
            if job_dir.exists():
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up job directory: {job_id}")
                return True
            else:
                logger.warning(f"Job directory not found for cleanup: {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Cleanup failed for job {job_id}: {e}", exc_info=True)
            return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up job directories older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of directories cleaned
        """
        import time
        
        try:
            cleaned = 0
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for job_dir in self.temp_dir.glob("job_*"):
                if job_dir.is_dir():
                    dir_age = current_time - job_dir.stat().st_mtime
                    
                    if dir_age > max_age_seconds:
                        shutil.rmtree(job_dir)
                        logger.info(f"Cleaned up old job directory: {job_dir.name}")
                        cleaned += 1
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old job directories")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Old job cleanup failed: {e}", exc_info=True)
            return 0


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get or create global file manager instance."""
    global _file_manager
    
    if _file_manager is None:
        # Get configuration from environment
        temp_dir = os.getenv("TEMP_UPLOAD_DIR", "temp")
        max_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
        
        _file_manager = FileManager(temp_dir=temp_dir, max_size_mb=max_size_mb)
    
    return _file_manager
