"""
Custom exception classes for the AI Video Agent application.
Provides specific error types for better error handling and debugging.
"""


class AIVideoAgentException(Exception):
    """Base exception for all AI Video Agent errors."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(AIVideoAgentException):
    """Raised when there's a configuration issue (missing env vars, invalid config, etc.)."""
    pass


class AudioProcessingError(AIVideoAgentException):
    """Raised when audio download, conversion, or chunking fails."""
    pass


class TranscriptionError(AIVideoAgentException):
    """Raised when transcription fails (Whisper or Sarvam API issues)."""
    pass


class LLMError(AIVideoAgentException):
    """Raised when LLM operations fail (Mistral API issues)."""
    pass


class VectorStoreError(AIVideoAgentException):
    """Raised when vector store operations fail."""
    pass


class ValidationError(AIVideoAgentException):
    """Raised when input validation fails."""
    pass


class ExternalAPIError(AIVideoAgentException):
    """Raised when external API calls fail (rate limits, timeouts, etc.)."""
    
    def __init__(self, message: str, api_name: str, status_code: int = None, details: dict = None):
        """
        Initialize the API error.
        
        Args:
            message: Error message
            api_name: Name of the API that failed (e.g., "Sarvam", "Mistral")
            status_code: HTTP status code if applicable
            details: Additional error context
        """
        self.api_name = api_name
        self.status_code = status_code
        error_details = details or {}
        error_details.update({
            "api": api_name,
            "status_code": status_code
        })
        super().__init__(message, error_details)


class ResourceCleanupError(AIVideoAgentException):
    """Raised when cleanup of temporary resources fails."""
    pass


class HealthCheckError(AIVideoAgentException):
    """Raised when health check fails."""
    pass
