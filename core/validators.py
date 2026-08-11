"""
Input validation and sanitization utilities for the AI Video Agent application.
Ensures all user inputs, file paths, URLs, and API responses are validated before processing.
"""

import os
import re
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
from core.exceptions import ValidationError
from core.logger import get_logger

logger = get_logger(__name__)


class InputValidator:
    """Comprehensive input validation for the application."""
    
    # Supported audio/video file extensions
    SUPPORTED_EXTENSIONS = {
        '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac',
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'
    }
    
    # Supported YouTube domains
    YOUTUBE_DOMAINS = {
        'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com'
    }
    
    # Maximum file size (500MB)
    MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024
    
    # Valid language options
    VALID_LANGUAGES = {'english', 'hinglish'}
    
    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate and sanitize a URL input.
        
        Args:
            url: URL string to validate
            
        Returns:
            Sanitized URL string
            
        Raises:
            ValidationError: If URL is invalid or not from supported domains
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")
        
        url = url.strip()
        
        # Basic URL format validation
        try:
            parsed = urlparse(url)
        except Exception as e:
            logger.error(f"Failed to parse URL: {url}")
            raise ValidationError(f"Invalid URL format: {str(e)}")
        
        if not parsed.scheme:
            raise ValidationError("URL must include a scheme (http:// or https://)")
        
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError(f"Unsupported URL scheme: {parsed.scheme}. Only http and https are allowed.")
        
        # Check if it's a YouTube URL
        if parsed.netloc.lower() in InputValidator.YOUTUBE_DOMAINS:
            logger.info(f"Validated YouTube URL: {parsed.netloc}")
            return url
        
        raise ValidationError(
            f"Unsupported domain: {parsed.netloc}. Only YouTube URLs are supported."
        )
    
    @staticmethod
    def validate_file_path(file_path: str) -> Path:
        """
        Validate and sanitize a local file path.
        
        Args:
            file_path: File path string to validate
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If file path is invalid, doesn't exist, or is not supported
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")
        
        file_path = file_path.strip()
        
        # Check for path traversal attempts
        if '..' in file_path or file_path.startswith('~'):
            # Resolve to absolute path for security
            try:
                resolved_path = Path(file_path).resolve()
            except Exception as e:
                raise ValidationError(f"Invalid file path: {str(e)}")
        else:
            resolved_path = Path(file_path).resolve()
        
        # Check if file exists
        if not resolved_path.exists():
            raise ValidationError(f"File does not exist: {resolved_path}")
        
        # Check if it's a file (not a directory)
        if not resolved_path.is_file():
            raise ValidationError(f"Path is not a file: {resolved_path}")
        
        # Check file extension
        if resolved_path.suffix.lower() not in InputValidator.SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file type: {resolved_path.suffix}. "
                f"Supported types: {', '.join(sorted(InputValidator.SUPPORTED_EXTENSIONS))}"
            )
        
        # Check file size
        file_size = resolved_path.stat().st_size
        if file_size > InputValidator.MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            max_mb = InputValidator.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise ValidationError(
                f"File too large: {size_mb:.1f}MB. Maximum allowed: {max_mb:.1f}MB"
            )
        
        logger.info(f"Validated file path: {resolved_path} ({file_size / (1024 * 1024):.1f}MB)")
        return resolved_path
    
    @staticmethod
    def validate_source_input(source: str) -> tuple[str, str]:
        """
        Validate source input and determine if it's a URL or file path.
        
        Args:
            source: User input (URL or file path)
            
        Returns:
            Tuple of (validated_source, source_type) where source_type is 'url' or 'file'
            
        Raises:
            ValidationError: If source is invalid
        """
        if not source or not isinstance(source, str):
            raise ValidationError("Source must be a non-empty string")
        
        source = source.strip()
        
        # Determine if it's a URL or file path
        if source.startswith(('http://', 'https://')):
            validated = InputValidator.validate_url(source)
            return validated, 'url'
        else:
            validated = str(InputValidator.validate_file_path(source))
            return validated, 'file'
    
    @staticmethod
    def validate_language(language: str) -> str:
        """
        Validate language input.
        
        Args:
            language: Language string
            
        Returns:
            Validated and normalized language string (lowercase)
            
        Raises:
            ValidationError: If language is not supported
        """
        if not language or not isinstance(language, str):
            raise ValidationError("Language must be a non-empty string")
        
        language = language.strip().lower()
        
        if language not in InputValidator.VALID_LANGUAGES:
            raise ValidationError(
                f"Unsupported language: {language}. "
                f"Supported languages: {', '.join(sorted(InputValidator.VALID_LANGUAGES))}"
            )
        
        return language
    
    @staticmethod
    def validate_chunk_minutes(chunk_minutes: int) -> int:
        """
        Validate chunk size in minutes.
        
        Args:
            chunk_minutes: Chunk size in minutes
            
        Returns:
            Validated chunk size
            
        Raises:
            ValidationError: If chunk size is invalid
        """
        if not isinstance(chunk_minutes, int):
            raise ValidationError("Chunk minutes must be an integer")
        
        if chunk_minutes < 1:
            raise ValidationError("Chunk minutes must be at least 1")
        
        if chunk_minutes > 30:
            raise ValidationError("Chunk minutes must not exceed 30 (for optimal processing)")
        
        return chunk_minutes
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename by removing potentially dangerous characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem operations
        """
        # Remove path separators and other dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed_file"
        
        # Limit length
        if len(sanitized) > 200:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:200-len(ext)] + ext
        
        return sanitized
    
    @staticmethod
    def validate_api_response(response_data: dict, required_fields: List[str]) -> dict:
        """
        Validate API response has required fields.
        
        Args:
            response_data: Response dictionary from API
            required_fields: List of required field names
            
        Returns:
            Validated response data
            
        Raises:
            ValidationError: If required fields are missing
        """
        if not isinstance(response_data, dict):
            raise ValidationError("API response must be a dictionary")
        
        missing_fields = [field for field in required_fields if field not in response_data]
        
        if missing_fields:
            raise ValidationError(
                f"API response missing required fields: {', '.join(missing_fields)}"
            )
        
        return response_data
    
    @staticmethod
    def validate_transcript(transcript: str) -> str:
        """
        Validate transcript text.
        
        Args:
            transcript: Transcript text
            
        Returns:
            Validated transcript
            
        Raises:
            ValidationError: If transcript is invalid
        """
        if not transcript or not isinstance(transcript, str):
            raise ValidationError("Transcript must be a non-empty string")
        
        transcript = transcript.strip()
        
        if len(transcript) < 10:
            raise ValidationError("Transcript is too short (minimum 10 characters)")
        
        if len(transcript) > 5_000_000:  # 5MB text limit
            raise ValidationError("Transcript is too long (maximum 5MB)")
        
        return transcript
    
    @staticmethod
    def validate_question(question: str) -> str:
        """
        Validate RAG chat question.
        
        Args:
            question: User question
            
        Returns:
            Validated and sanitized question
            
        Raises:
            ValidationError: If question is invalid
        """
        if not question or not isinstance(question, str):
            raise ValidationError("Question must be a non-empty string")
        
        question = question.strip()
        
        if len(question) < 3:
            raise ValidationError("Question is too short (minimum 3 characters)")
        
        if len(question) > 1000:
            raise ValidationError("Question is too long (maximum 1000 characters)")
        
        return question
