"""
Robust Mistral API Client with Rate Limiting and Retry Logic.
Handles 429 errors, exponential backoff, and proper error propagation.
"""

import os
import time
import random
from typing import Optional, Any, Dict
from functools import wraps

try:
    from langchain_mistralai import ChatMistralAI
except ImportError as e:
    ChatMistralAI = None
    logger = None
    MISTRAL_AVAILABLE = False
    _MISTRAL_IMPORT_ERROR = e
else:
    MISTRAL_AVAILABLE = True
    _MISTRAL_IMPORT_ERROR = None

try:
    from mistralai.exceptions import MistralAPIException, MistralException
except ImportError:
    MistralAPIException = Exception
    MistralException = Exception

from core.logger import get_logger

logger = get_logger(__name__)


class MistralRateLimitError(Exception):
    """Raised when Mistral API rate limit is exceeded after all retries."""
    pass


class MistralClient:
    """
    Wrapper for Mistral LLM with automatic rate limiting and retry logic.
    """
    
    def __init__(
        self,
        model: str = "mistral-small-latest",
        temperature: float = 0.3,
        max_retries: int = 5,
        initial_retry_delay: float = 2.0,
        max_retry_delay: float = 60.0,
        timeout: int = 120
    ):
        """
        Initialize Mistral client with retry configuration.
        
        Args:
            model: Mistral model name
            temperature: Temperature for generation
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial delay in seconds before first retry
            max_retry_delay: Maximum delay between retries
            timeout: Request timeout in seconds
        """
        if not MISTRAL_AVAILABLE:
            raise ImportError(
                "Mistral dependencies not available. "
                "Install with: pip install langchain-mistralai mistralai"
            )
        
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.timeout = timeout
        
        # Get API key
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "MISTRAL_API_KEY not found in environment. "
                "Please set it in your .env file."
            )
        
        # Log configuration (without exposing key)
        logger.info(f"[MistralClient] Initialized: model={model}, temp={temperature}, "
                   f"max_retries={max_retries}")
    
    def _get_llm(self, **kwargs) -> ChatMistralAI:
        """Create LLM instance with configured parameters."""
        params = {
            "model": self.model,
            "mistral_api_key": self.api_key,
            "temperature": self.temperature,
            "timeout": self.timeout,
        }
        params.update(kwargs)
        return ChatMistralAI(**params)
    
    def _calculate_retry_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """
        Calculate delay before next retry with exponential backoff and jitter.
        
        Args:
            attempt: Current retry attempt number (0-indexed)
            retry_after: Optional Retry-After header value in seconds
            
        Returns:
            Delay in seconds
        """
        if retry_after:
            # Respect Retry-After header
            delay = retry_after
        else:
            # Exponential backoff: delay = initial * (2 ^ attempt)
            delay = self.initial_retry_delay * (2 ** attempt)
        
        # Cap at maximum delay
        delay = min(delay, self.max_retry_delay)
        
        # Add jitter (±25% random variation)
        jitter = delay * 0.25 * (random.random() * 2 - 1)
        delay = delay + jitter
        
        return max(0.1, delay)  # Minimum 0.1 seconds
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error should be retried
        """
        error_str = str(error).lower()
        
        # Retryable: Rate limits, timeouts, server errors
        retryable_patterns = [
            "429",
            "rate limit",
            "rate_limited",
            "timeout",
            "timed out",
            "503",
            "service unavailable",
            "500",
            "internal server error",
            "connection",
            "network"
        ]
        
        # Non-retryable: Auth errors, invalid requests
        non_retryable_patterns = [
            "401",
            "unauthorized",
            "403",
            "forbidden",
            "invalid api key",
            "400",
            "bad request",
            "invalid_request"
        ]
        
        # Check non-retryable first
        for pattern in non_retryable_patterns:
            if pattern in error_str:
                return False
        
        # Check retryable
        for pattern in retryable_patterns:
            if pattern in error_str:
                return True
        
        # Default: retry on unknown errors
        return True
    
    def _extract_retry_after(self, error: Exception) -> Optional[float]:
        """
        Extract Retry-After value from error if available.
        
        Args:
            error: Exception that may contain Retry-After info
            
        Returns:
            Retry-After value in seconds, or None
        """
        # Try to extract from Mistral API exception
        if hasattr(error, 'http_status') and hasattr(error, 'headers'):
            headers = getattr(error, 'headers', {})
            if isinstance(headers, dict):
                retry_after = headers.get('Retry-After') or headers.get('retry-after')
                if retry_after:
                    try:
                        return float(retry_after)
                    except (ValueError, TypeError):
                        pass
        
        return None
    
    def invoke_with_retry(
        self,
        chain: Any,
        input_data: Any,
        operation_name: str = "LLM operation"
    ) -> Any:
        """
        Invoke a LangChain chain with automatic retry logic.
        
        Args:
            chain: LangChain chain to invoke
            input_data: Input data for the chain
            operation_name: Human-readable operation name for logging
            
        Returns:
            Chain output
            
        Raises:
            MistralRateLimitError: If rate limit exceeded after all retries
            Exception: For non-retryable errors
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Log attempt
                if attempt == 0:
                    logger.debug(f"[Mistral] {operation_name}: Starting")
                else:
                    logger.info(f"[Mistral] {operation_name}: Retry {attempt}/{self.max_retries}")
                
                # Invoke chain
                result = chain.invoke(input_data)
                
                # Success
                if attempt > 0:
                    logger.info(f"[Mistral] {operation_name}: Succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Check if retryable
                is_retryable = self._is_retryable_error(e)
                
                # Check if rate limit error
                is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
                
                if not is_retryable:
                    logger.error(f"[Mistral] {operation_name}: Non-retryable error: {error_str}")
                    raise
                
                if attempt >= self.max_retries:
                    # Out of retries
                    if is_rate_limit:
                        logger.error(
                            f"[Mistral] {operation_name}: Rate limit exceeded after "
                            f"{self.max_retries} retries"
                        )
                        raise MistralRateLimitError(
                            f"Mistral API rate limit exceeded after {self.max_retries} retries. "
                            f"Please wait a few minutes and try again."
                        ) from e
                    else:
                        logger.error(
                            f"[Mistral] {operation_name}: Failed after {self.max_retries} retries: "
                            f"{error_str}"
                        )
                        raise
                
                # Calculate retry delay
                retry_after = self._extract_retry_after(e)
                delay = self._calculate_retry_delay(attempt, retry_after)
                
                # Log retry
                if is_rate_limit:
                    logger.warning(
                        f"[Mistral] {operation_name}: Rate limit hit (429). "
                        f"Waiting {delay:.1f}s before retry {attempt + 1}/{self.max_retries}"
                    )
                else:
                    logger.warning(
                        f"[Mistral] {operation_name}: Error: {error_str}. "
                        f"Waiting {delay:.1f}s before retry {attempt + 1}/{self.max_retries}"
                    )
                
                # Wait before retry
                time.sleep(delay)
        
        # Should never reach here, but just in case
        raise last_error


# Global client instance
_mistral_client: Optional[MistralClient] = None


def get_mistral_client(
    model: str = "mistral-small-latest",
    temperature: float = 0.3,
    **kwargs
) -> MistralClient:
    """
    Get or create global Mistral client instance.
    
    Args:
        model: Mistral model name
        temperature: Generation temperature
        **kwargs: Additional client parameters
        
    Returns:
        MistralClient instance
    """
    global _mistral_client
    
    # Create new client if not exists or parameters changed
    if _mistral_client is None:
        _mistral_client = MistralClient(
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    return _mistral_client


def get_llm(model: str = "mistral-small-latest", temperature: float = 0.3, **kwargs):
    """
    Get Mistral LLM instance (backward compatible helper).
    
    Args:
        model: Model name
        temperature: Temperature
        **kwargs: Additional parameters
        
    Returns:
        ChatMistralAI instance
    """
    if not MISTRAL_AVAILABLE:
        return None
    
    client = get_mistral_client(model=model, temperature=temperature, **kwargs)
    return client._get_llm()
