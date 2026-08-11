"""
Centralized logging configuration for the AI Video Agent application.
Provides structured logging with rotation, different log levels, and both file and console output.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggerConfig:
    """Centralized logging configuration with file rotation and console output."""
    
    _loggers = {}
    
    @staticmethod
    def setup_logger(
        name: str,
        log_level: str = "INFO",
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Set up a logger with both file and console handlers.
        
        Args:
            name: Logger name (typically __name__ of the module)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory to store log files
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup files to keep
            
        Returns:
            Configured logger instance
        """
        if name in LoggerConfig._loggers:
            return LoggerConfig._loggers[name]
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Define log format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = log_path / f"{name.replace('.', '_')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error file handler (separate file for errors)
        error_log_file = log_path / f"{name.replace('.', '_')}_errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        LoggerConfig._loggers[name] = logger
        return logger
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get an existing logger or create a new one with default settings."""
        if name not in LoggerConfig._loggers:
            log_level = os.getenv("LOG_LEVEL", "INFO")
            return LoggerConfig.setup_logger(name, log_level=log_level)
        return LoggerConfig._loggers[name]
    
    @staticmethod
    def sanitize_message(message: str, sensitive_keys: list = None) -> str:
        """
        Remove sensitive information from log messages.
        
        Args:
            message: Original log message
            sensitive_keys: List of sensitive keywords to redact
            
        Returns:
            Sanitized message with sensitive data masked
        """
        if sensitive_keys is None:
            sensitive_keys = ["api_key", "apikey", "password", "token", "secret", "auth"]
        
        sanitized = message
        for key in sensitive_keys:
            # Simple regex-based redaction
            import re
            pattern = re.compile(f"({key}[\"']?\s*[:=]\s*[\"']?)([^\"',\\s]+)", re.IGNORECASE)
            sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
        
        return sanitized


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger instance."""
    return LoggerConfig.get_logger(name)
