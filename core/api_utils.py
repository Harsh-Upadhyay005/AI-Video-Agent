"""
API utilities for handling external API calls with retry logic, rate limiting, and error handling.
Provides robust wrappers for Mistral and Sarvam API calls.
"""

import time
import functools
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import requests
from core.exceptions import ExternalAPIError
from core.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Simple rate limiter to prevent exceeding API rate limits.
    Uses a sliding window approach.
    """
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply rate limiting to a function."""
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            
            # Remove calls outside the time window
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < timedelta(seconds=self.time_window)]
            
            # Check if we've exceeded the rate limit
            if len(self.calls) >= self.max_calls:
                oldest_call = min(self.calls)
                sleep_time = (oldest_call + timedelta(seconds=self.time_window) - now).total_seconds()
                
                if sleep_time > 0:
                    logger.warning(
                        f"Rate limit reached for {func.__name__}. "
                        f"Sleeping for {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)
                    # Clean up old calls again
                    now = datetime.now()
                    self.calls = [call_time for call_time in self.calls 
                                 if now - call_time < timedelta(seconds=self.time_window)]
            
            # Record this call
            self.calls.append(now)
            
            # Execute the function
            return func(*args, **kwargs)
        
        return wrapper


class RetryHandler:
    """
    Retry handler with exponential backoff for API calls.
    Handles transient errors gracefully.
    """
    
    # HTTP status codes that should trigger a retry
    RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
    
    # Network errors that should trigger a retry
    RETRYABLE_EXCEPTIONS = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    )
    
    @staticmethod
    def exponential_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        api_name: str = "API"
    ) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            api_name: Name of the API for logging purposes
            
        Returns:
            Result of the function call
            
        Raises:
            ExternalAPIError: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                result = func()
                
                if attempt > 0:
                    logger.info(f"{api_name} call succeeded on attempt {attempt + 1}")
                
                return result
                
            except RetryHandler.RETRYABLE_EXCEPTIONS as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        f"{api_name} call failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                    )
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(
                        f"{api_name} call failed after {max_retries + 1} attempts: {str(e)}"
                    )
            
            except requests.exceptions.HTTPError as e:
                # Check if status code is retryable
                if hasattr(e.response, 'status_code'):
                    status_code = e.response.status_code
                    
                    if status_code in RetryHandler.RETRYABLE_STATUS_CODES:
                        last_exception = e
                        
                        if attempt < max_retries:
                            delay = min(base_delay * (exponential_base ** attempt), max_delay)
                            logger.warning(
                                f"{api_name} returned status {status_code} "
                                f"(attempt {attempt + 1}/{max_retries + 1})"
                            )
                            logger.info(f"Retrying in {delay:.2f} seconds...")
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"{api_name} failed with status {status_code} "
                                f"after {max_retries + 1} attempts"
                            )
                    else:
                        # Non-retryable status code
                        logger.error(f"{api_name} returned non-retryable status {status_code}")
                        raise ExternalAPIError(
                            f"{api_name} request failed with status {status_code}",
                            api_name=api_name,
                            status_code=status_code,
                            details={"error": str(e)}
                        )
                else:
                    raise
            
            except Exception as e:
                # Non-retryable exception
                logger.error(f"{api_name} call failed with non-retryable error: {str(e)}")
                raise ExternalAPIError(
                    f"{api_name} request failed: {str(e)}",
                    api_name=api_name,
                    details={"error": str(e), "type": type(e).__name__}
                )
        
        # All retries exhausted
        raise ExternalAPIError(
            f"{api_name} request failed after {max_retries + 1} attempts",
            api_name=api_name,
            details={"last_error": str(last_exception)}
        )
    
    @staticmethod
    def retry_on_exception(
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        api_name: str = "API"
    ):
        """
        Decorator for adding retry logic to functions.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            api_name: Name of the API for logging purposes
            
        Returns:
            Decorated function with retry logic
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return RetryHandler.exponential_backoff(
                    lambda: func(*args, **kwargs),
                    max_retries=max_retries,
                    base_delay=base_delay,
                    max_delay=max_delay,
                    exponential_base=exponential_base,
                    api_name=api_name
                )
            return wrapper
        return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures.
    Stops making requests to a failing service temporarily.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to a function."""
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check circuit state
            if self.state == "open":
                if self.last_failure_time:
                    elapsed = time.time() - self.last_failure_time
                    if elapsed > self.recovery_timeout:
                        logger.info(
                            f"Circuit breaker for {func.__name__} entering half-open state"
                        )
                        self.state = "half_open"
                    else:
                        raise ExternalAPIError(
                            f"Circuit breaker is open for {func.__name__}. "
                            f"Service is temporarily unavailable. "
                            f"Retry in {self.recovery_timeout - elapsed:.0f} seconds.",
                            api_name=func.__name__
                        )
            
            try:
                result = func(*args, **kwargs)
                
                # Success - reset failure count
                if self.state == "half_open":
                    logger.info(f"Circuit breaker for {func.__name__} closing (recovered)")
                    self.state = "closed"
                
                self.failure_count = 0
                return result
                
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                logger.warning(
                    f"Circuit breaker failure {self.failure_count}/{self.failure_threshold} "
                    f"for {func.__name__}"
                )
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error(
                        f"Circuit breaker for {func.__name__} opened due to repeated failures"
                    )
                
                raise
        
        return wrapper


class APICallLogger:
    """Logs API calls for monitoring and debugging."""
    
    @staticmethod
    def log_api_call(
        api_name: str,
        endpoint: str,
        method: str = "POST",
        response_time: Optional[float] = None,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Log an API call with relevant metrics.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint
            method: HTTP method
            response_time: Response time in seconds
            status_code: HTTP status code
            error: Error message if call failed
        """
        log_data = {
            "api": api_name,
            "endpoint": endpoint,
            "method": method
        }
        
        if response_time is not None:
            log_data["response_time_ms"] = f"{response_time * 1000:.2f}"
        
        if status_code is not None:
            log_data["status_code"] = status_code
        
        if error:
            log_data["error"] = error
            logger.error(f"API call failed: {log_data}")
        else:
            logger.info(f"API call succeeded: {log_data}")
    
    @staticmethod
    def api_call_decorator(api_name: str, endpoint: str = ""):
        """
        Decorator to automatically log API calls.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint (optional)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                error_msg = None
                status_code = None
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Try to extract status code if result is a response object
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                    
                    return result
                    
                except Exception as e:
                    error_msg = str(e)
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        status_code = e.response.status_code
                    raise
                    
                finally:
                    response_time = time.time() - start_time
                    APICallLogger.log_api_call(
                        api_name=api_name,
                        endpoint=endpoint or func.__name__,
                        response_time=response_time,
                        status_code=status_code,
                        error=error_msg
                    )
            
            return wrapper
        return decorator


# Convenient combined decorator
def robust_api_call(
    api_name: str,
    max_retries: int = 3,
    rate_limit_calls: Optional[int] = None,
    rate_limit_window: Optional[int] = None,
    enable_circuit_breaker: bool = False
):
    """
    Combined decorator for robust API calls with retry, rate limiting, and circuit breaker.
    
    Args:
        api_name: Name of the API
        max_retries: Maximum retry attempts
        rate_limit_calls: Maximum calls per time window (None to disable)
        rate_limit_window: Time window for rate limiting in seconds
        enable_circuit_breaker: Enable circuit breaker pattern
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        wrapped_func = func
        
        # Apply retry logic
        wrapped_func = RetryHandler.retry_on_exception(
            max_retries=max_retries,
            api_name=api_name
        )(wrapped_func)
        
        # Apply rate limiting if specified
        if rate_limit_calls and rate_limit_window:
            wrapped_func = RateLimiter(
                max_calls=rate_limit_calls,
                time_window=rate_limit_window
            )(wrapped_func)
        
        # Apply circuit breaker if enabled
        if enable_circuit_breaker:
            wrapped_func = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=60
            )(wrapped_func)
        
        # Apply API call logging
        wrapped_func = APICallLogger.api_call_decorator(api_name)(wrapped_func)
        
        return wrapped_func
    
    return decorator
