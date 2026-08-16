"""
Global Metadata Storage for Video-Level Information.
Stores summaries, topics, and structured information about entire videos.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class VideoSection:
    """Represents a logical section of the video."""
    title: str
    summary: str
    start_time: float  # seconds
    end_time: float  # seconds
    key_points: List[str]


@dataclass
class VideoMetadata:
    """Global metadata for a video/audio source."""
    video_id: str  # Unique identifier (job_id, URL hash, etc.)
    source: str  # Original source (YouTube URL, filename, etc.)
    source_type: str  # youtube, mp3, mp4
    duration: Optional[float]  # Total duration in seconds
    
    # Global information
    title: str
    summary: str  # Overall summary
    topics: List[str]  # Main topics discussed
    key_concepts: List[str]  # Important concepts
    
    # Structured sections (optional)
    sections: List[VideoSection]
    
    # Metadata
    created_at: str
    transcript_length: int  # Character count
    chunk_count: int  # Number of chunks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert nested dataclasses
        data['sections'] = [asdict(s) for s in self.sections]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoMetadata':
        """Create from dictionary."""
        # Convert sections back to VideoSection objects
        sections = [VideoSection(**s) for s in data.get('sections', [])]
        data['sections'] = sections
        return cls(**data)


class GlobalMetadataStore:
    """
    Stores and retrieves global metadata for videos.
    Uses JSON file storage (can be upgraded to database later).
    """
    
    def __init__(self, storage_dir: str = "metadata_store"):
        """
        Initialize metadata store.
        
        Args:
            storage_dir: Directory to store metadata files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, video_id: str) -> Path:
        """Get file path for a video's metadata."""
        # Sanitize video_id for filename
        safe_id = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in video_id)
        return self.storage_dir / f"{safe_id}.json"
    
    def save(self, metadata: VideoMetadata) -> None:
        """
        Save video metadata.
        
        Args:
            metadata: VideoMetadata to save
        """
        file_path = self._get_file_path(metadata.video_id)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"[GlobalMetadataStore] Saved metadata for {metadata.video_id}")
        except Exception as e:
            print(f"[GlobalMetadataStore] Error saving metadata: {e}")
    
    def load(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Load video metadata.
        
        Args:
            video_id: Video identifier
            
        Returns:
            VideoMetadata if found, None otherwise
        """
        file_path = self._get_file_path(video_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return VideoMetadata.from_dict(data)
        except Exception as e:
            print(f"[GlobalMetadataStore] Error loading metadata: {e}")
            return None
    
    def exists(self, video_id: str) -> bool:
        """Check if metadata exists for a video."""
        return self._get_file_path(video_id).exists()
    
    def delete(self, video_id: str) -> bool:
        """
        Delete metadata for a video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(video_id)
        
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"[GlobalMetadataStore] Deleted metadata for {video_id}")
                return True
            except Exception as e:
                print(f"[GlobalMetadataStore] Error deleting metadata: {e}")
                return False
        return False
    
    def list_all(self) -> List[str]:
        """List all video IDs with metadata."""
        try:
            return [
                f.stem for f in self.storage_dir.glob("*.json")
            ]
        except Exception as e:
            print(f"[GlobalMetadataStore] Error listing metadata: {e}")
            return []


# Global instance
_metadata_store = None


def get_metadata_store() -> GlobalMetadataStore:
    """Get singleton metadata store instance."""
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = GlobalMetadataStore()
    return _metadata_store


def save_video_metadata(metadata: VideoMetadata) -> None:
    """Convenience function to save metadata."""
    store = get_metadata_store()
    store.save(metadata)


def load_video_metadata(video_id: str) -> Optional[VideoMetadata]:
    """Convenience function to load metadata."""
    store = get_metadata_store()
    return store.load(video_id)
