"""
Resource management utilities for cleanup and memory management.
Ensures temporary files are cleaned up and resources are properly released.
"""

import os
import gc
import shutil
from pathlib import Path
from typing import List, Optional, Set
from contextlib import contextmanager
from datetime import datetime, timedelta
from core.logger import get_logger
from core.exceptions import ResourceCleanupError

logger = get_logger(__name__)


class ResourceManager:
    """
    Manages temporary resources and ensures proper cleanup.
    Tracks created files and provides automatic cleanup.
    """
    
    def __init__(self):
        """Initialize resource manager."""
        self._tracked_files: Set[Path] = set()
        self._tracked_dirs: Set[Path] = set()
    
    def track_file(self, file_path: str) -> Path:
        """
        Track a file for cleanup.
        
        Args:
            file_path: Path to file to track
            
        Returns:
            Path object
        """
        path = Path(file_path)
        self._tracked_files.add(path)
        logger.debug(f"Tracking file: {path}")
        return path
    
    def track_directory(self, dir_path: str) -> Path:
        """
        Track a directory for cleanup.
        
        Args:
            dir_path: Path to directory to track
            
        Returns:
            Path object
        """
        path = Path(dir_path)
        self._tracked_dirs.add(path)
        logger.debug(f"Tracking directory: {path}")
        return path
    
    def untrack_file(self, file_path: str):
        """
        Stop tracking a file (e.g., if it should be kept).
        
        Args:
            file_path: Path to file to untrack
        """
        path = Path(file_path)
        self._tracked_files.discard(path)
        logger.debug(f"Untracked file: {path}")
    
    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a single file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successfully deleted
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug(f"Deleted file: {path}")
                self._tracked_files.discard(path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def cleanup_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """
        Clean up a directory.
        
        Args:
            dir_path: Path to directory to delete
            recursive: If True, delete recursively
            
        Returns:
            True if successfully deleted
        """
        try:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                if recursive:
                    shutil.rmtree(path)
                else:
                    path.rmdir()
                logger.debug(f"Deleted directory: {path}")
                self._tracked_dirs.discard(path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete directory {dir_path}: {str(e)}")
            return False
    
    def cleanup_all(self) -> dict:
        """
        Clean up all tracked resources.
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "files_deleted": 0,
            "files_failed": 0,
            "dirs_deleted": 0,
            "dirs_failed": 0
        }
        
        # Clean up files
        for file_path in list(self._tracked_files):
            if self.cleanup_file(str(file_path)):
                stats["files_deleted"] += 1
            else:
                stats["files_failed"] += 1
        
        # Clean up directories
        for dir_path in list(self._tracked_dirs):
            if self.cleanup_directory(str(dir_path)):
                stats["dirs_deleted"] += 1
            else:
                stats["dirs_failed"] += 1
        
        logger.info(f"Cleanup complete: {stats}")
        return stats
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup_all()
        return False


class TempFileManager:
    """
    Manages temporary files with automatic cleanup.
    Provides context managers for temporary file operations.
    """
    
    @staticmethod
    @contextmanager
    def temporary_file(suffix: str = "", prefix: str = "temp_", directory: Optional[str] = None):
        """
        Context manager for creating and automatically cleaning up a temporary file.
        
        Args:
            suffix: File suffix (e.g., ".wav")
            prefix: File prefix
            directory: Directory to create file in (default: system temp)
            
        Yields:
            Path to temporary file
        """
        import tempfile
        
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory)
        os.close(fd)
        
        temp_file = Path(temp_path)
        logger.debug(f"Created temporary file: {temp_file}")
        
        try:
            yield temp_file
        finally:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary file {temp_file}: {str(e)}")
    
    @staticmethod
    @contextmanager
    def temporary_directory(prefix: str = "temp_", directory: Optional[str] = None):
        """
        Context manager for creating and automatically cleaning up a temporary directory.
        
        Args:
            prefix: Directory prefix
            directory: Parent directory (default: system temp)
            
        Yields:
            Path to temporary directory
        """
        import tempfile
        
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=directory))
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        try:
            yield temp_dir
        finally:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary directory {temp_dir}: {str(e)}")


class DirectoryCleanup:
    """
    Utilities for cleaning up old files from application directories.
    Useful for managing downloads, logs, and other temporary data.
    """
    
    @staticmethod
    def cleanup_old_files(
        directory: str,
        max_age_days: int = 7,
        pattern: str = "*",
        dry_run: bool = False
    ) -> dict:
        """
        Delete files older than specified age from a directory.
        
        Args:
            directory: Directory to clean
            max_age_days: Delete files older than this many days
            pattern: Glob pattern for files to consider (e.g., "*.wav")
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "total_files": 0,
            "deleted_count": 0,
            "deleted_size_mb": 0,
            "failed_count": 0,
            "files": []
        }
        
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return stats
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            stats["total_files"] += 1
            
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    
                    if dry_run:
                        logger.info(f"Would delete: {file_path} ({file_size_mb:.2f} MB)")
                        stats["files"].append(str(file_path))
                    else:
                        file_path.unlink()
                        logger.info(f"Deleted old file: {file_path} ({file_size_mb:.2f} MB)")
                        stats["deleted_count"] += 1
                        stats["deleted_size_mb"] += file_size_mb
                        stats["files"].append(str(file_path))
                        
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {str(e)}")
                stats["failed_count"] += 1
        
        return stats
    
    @staticmethod
    def cleanup_application_dirs(max_age_days: int = 7, dry_run: bool = False) -> dict:
        """
        Clean up all application temporary directories.
        
        Args:
            max_age_days: Delete files older than this many days
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary with cleanup statistics for each directory
        """
        results = {}
        
        # Directories to clean
        dirs_to_clean = [
            ("downloads", "*.wav"),
            ("downloads", "*.mp3"),
            ("downloads", "*.mp4"),
            ("downloads", "*.webm"),
            ("logs", "*.log.*"),  # Backup log files
        ]
        
        for directory, pattern in dirs_to_clean:
            if Path(directory).exists():
                logger.info(f"Cleaning {directory} ({pattern})...")
                stats = DirectoryCleanup.cleanup_old_files(
                    directory,
                    max_age_days=max_age_days,
                    pattern=pattern,
                    dry_run=dry_run
                )
                results[f"{directory}/{pattern}"] = stats
        
        return results


class MemoryManager:
    """
    Memory management utilities for monitoring and optimizing memory usage.
    """
    
    @staticmethod
    def get_memory_usage() -> dict:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        import psutil
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024)
        }
    
    @staticmethod
    def log_memory_usage(label: str = ""):
        """
        Log current memory usage.
        
        Args:
            label: Optional label for the log entry
        """
        try:
            memory = MemoryManager.get_memory_usage()
            prefix = f"[{label}] " if label else ""
            logger.info(
                f"{prefix}Memory usage: "
                f"RSS={memory['rss_mb']:.1f}MB, "
                f"VMS={memory['vms_mb']:.1f}MB, "
                f"Percent={memory['percent']:.1f}%, "
                f"Available={memory['available_mb']:.1f}MB"
            )
        except ImportError:
            logger.warning("psutil not installed - memory monitoring unavailable")
        except Exception as e:
            logger.error(f"Failed to get memory usage: {str(e)}")
    
    @staticmethod
    def force_garbage_collection():
        """
        Force garbage collection to free up memory.
        
        Returns:
            Number of objects collected
        """
        logger.debug("Running garbage collection...")
        collected = gc.collect()
        logger.debug(f"Garbage collection complete. Collected {collected} objects.")
        return collected
    
    @staticmethod
    @contextmanager
    def memory_monitor(label: str = "Operation"):
        """
        Context manager for monitoring memory usage during an operation.
        
        Args:
            label: Label for the operation
            
        Yields:
            None
        """
        logger.info(f"Starting memory monitoring: {label}")
        MemoryManager.log_memory_usage(f"{label} - Before")
        
        try:
            yield
        finally:
            MemoryManager.log_memory_usage(f"{label} - After")
            MemoryManager.force_garbage_collection()
            MemoryManager.log_memory_usage(f"{label} - After GC")


# Global resource manager instance
_global_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """
    Get the global resource manager instance.
    
    Returns:
        ResourceManager instance
    """
    global _global_resource_manager
    if _global_resource_manager is None:
        _global_resource_manager = ResourceManager()
    return _global_resource_manager


def cleanup_on_shutdown():
    """
    Cleanup function to be called on application shutdown.
    Cleans up all tracked resources.
    """
    logger.info("Running shutdown cleanup...")
    manager = get_resource_manager()
    stats = manager.cleanup_all()
    logger.info(f"Shutdown cleanup complete: {stats}")
