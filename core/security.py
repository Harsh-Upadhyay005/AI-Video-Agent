"""
Security utilities for the AI Video Agent application.
Handles sensitive data sanitization, secure logging, and secrets management.
"""

import re
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from core.logger import get_logger

logger = get_logger(__name__)


class SecretsManager:
    """
    Manages sensitive configuration and prevents accidental exposure.
    Provides utilities for sanitizing logs and validating secrets.
    """
    
    # Patterns to detect sensitive information
    SENSITIVE_PATTERNS = [
        (r'(api[_-]?key[\s=:]+)["\']?([a-zA-Z0-9_\-]+)["\']?', r'\1***REDACTED***'),
        (r'(apikey[\s=:]+)["\']?([a-zA-Z0-9_\-]+)["\']?', r'\1***REDACTED***'),
        (r'(password[\s=:]+)["\']?([^\s"\']+)["\']?', r'\1***REDACTED***'),
        (r'(token[\s=:]+)["\']?([a-zA-Z0-9_\-\.]+)["\']?', r'\1***REDACTED***'),
        (r'(secret[\s=:]+)["\']?([^\s"\']+)["\']?', r'\1***REDACTED***'),
        (r'(auth[\s=:]+)["\']?([^\s"\']+)["\']?', r'\1***REDACTED***'),
        (r'(bearer\s+)([a-zA-Z0-9_\-\.]+)', r'\1***REDACTED***'),
        (r'([a-zA-Z0-9_]+@[a-zA-Z0-9_]+\.[a-zA-Z]{2,})', r'***EMAIL_REDACTED***'),
    ]
    
    # Environment variable keys that contain sensitive data
    SENSITIVE_ENV_KEYS = {
        'MISTRAL_API_KEY',
        'SARVAM_ANON_KEY',
        'API_KEY',
        'SECRET_KEY',
        'PASSWORD',
        'TOKEN',
        'AUTH_TOKEN',
        'DATABASE_URL',
        'DB_PASSWORD',
    }
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """
        Remove sensitive information from a string using regex patterns.
        
        Args:
            text: Text that may contain sensitive information
            
        Returns:
            Sanitized text with sensitive data redacted
        """
        if not text:
            return text
        
        sanitized = text
        for pattern, replacement in SecretsManager.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
        """
        Sanitize a dictionary by redacting sensitive values.
        
        Args:
            data: Dictionary that may contain sensitive information
            recursive: If True, recursively sanitize nested dictionaries
            
        Returns:
            Dictionary with sensitive values redacted
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            # Check if key indicates sensitive data
            if any(sensitive_key.lower() in key.lower() 
                   for sensitive_key in ['api_key', 'password', 'token', 'secret', 'auth']):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict) and recursive:
                sanitized[key] = SecretsManager.sanitize_dict(value, recursive=True)
            elif isinstance(value, str):
                sanitized[key] = SecretsManager.sanitize_string(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [
                    SecretsManager.sanitize_dict(item, recursive=True) if isinstance(item, dict)
                    else SecretsManager.sanitize_string(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key showing only the first few and last few characters.
        
        Args:
            api_key: API key to mask
            visible_chars: Number of characters to show at start and end
            
        Returns:
            Masked API key (e.g., "sk_1234...7890")
        """
        if not api_key or len(api_key) <= visible_chars * 2:
            return '***REDACTED***'
        
        prefix = api_key[:visible_chars]
        suffix = api_key[-visible_chars:]
        return f"{prefix}...{suffix}"
    
    @staticmethod
    def validate_api_key_format(api_key: str, min_length: int = 16) -> bool:
        """
        Validate that an API key meets basic format requirements.
        
        Args:
            api_key: API key to validate
            min_length: Minimum expected length
            
        Returns:
            True if key appears valid
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Check length
        if len(api_key) < min_length:
            return False
        
        # Check for placeholder values
        placeholder_patterns = [
            'your_api_key',
            'your_key_here',
            'replace_me',
            'xxxxx',
            'example',
        ]
        
        if any(pattern in api_key.lower() for pattern in placeholder_patterns):
            return False
        
        # Check for only alphanumeric and common special chars
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', api_key):
            return False
        
        return True
    
    @staticmethod
    def get_safe_env_summary() -> Dict[str, str]:
        """
        Get a summary of environment variables with sensitive values masked.
        
        Returns:
            Dictionary of environment variables with sensitive data masked
        """
        safe_env = {}
        
        for key, value in os.environ.items():
            # Check if this is a sensitive key
            if any(sensitive in key.upper() for sensitive in ['KEY', 'PASSWORD', 'TOKEN', 'SECRET', 'AUTH']):
                if value:
                    safe_env[key] = SecretsManager.mask_api_key(value)
                else:
                    safe_env[key] = 'NOT_SET'
            else:
                safe_env[key] = value
        
        return safe_env
    
    @staticmethod
    def check_env_file_security(env_file: str = ".env") -> List[str]:
        """
        Check .env file for security issues.
        
        Args:
            env_file: Path to .env file
            
        Returns:
            List of security warnings/issues found
        """
        issues = []
        env_path = Path(env_file)
        
        if not env_path.exists():
            return ["No .env file found"]
        
        # Check file permissions (Unix-like systems)
        if hasattr(os, 'stat'):
            try:
                stat_info = env_path.stat()
                # Check if file is readable by others (on Unix)
                if hasattr(stat_info, 'st_mode'):
                    # 0o004 is read permission for others
                    if stat_info.st_mode & 0o004:
                        issues.append(
                            "[warning]  .env file is readable by others. "
                            "Restrict permissions: chmod 600 .env"
                        )
            except Exception:
                pass
        
        # Check if .env is in .gitignore
        gitignore_path = Path(".gitignore")
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            if ".env" not in gitignore_content:
                issues.append(
                    "[warning]  .env is not in .gitignore. "
                    "Add it to prevent accidental commits!"
                )
        else:
            issues.append("[warning]  No .gitignore file found")
        
        # Check for placeholder values in .env
        try:
            env_content = env_path.read_text()
            placeholder_patterns = [
                'your_api_key_here',
                'your_key_here',
                'replace_me',
                'example',
            ]
            
            for pattern in placeholder_patterns:
                if pattern.lower() in env_content.lower():
                    issues.append(
                        f"⚠️  .env file contains placeholder value '{pattern}'. "
                        "Replace with actual values."
                    )
                    break
        except Exception as e:
            issues.append(f"⚠️  Could not read .env file: {str(e)}")
        
        return issues
    
    @staticmethod
    def validate_secrets(required_secrets: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate that all required secrets are properly configured.
        
        Args:
            required_secrets: List of required environment variable names
            
        Returns:
            Dictionary with validation results
        """
        if required_secrets is None:
            required_secrets = ['MISTRAL_API_KEY']
        
        results = {
            "valid": True,
            "missing": [],
            "invalid": [],
            "warnings": []
        }
        
        for secret_name in required_secrets:
            value = os.getenv(secret_name)
            
            if not value:
                results["missing"].append(secret_name)
                results["valid"] = False
            elif not SecretsManager.validate_api_key_format(value):
                results["invalid"].append(secret_name)
                results["valid"] = False
                logger.warning(f"Secret {secret_name} appears to have invalid format")
        
        # Check for security issues in .env file
        env_issues = SecretsManager.check_env_file_security()
        if env_issues:
            results["warnings"].extend(env_issues)
        
        return results


class SecureLogger:
    """
    Wrapper for logging that automatically sanitizes sensitive information.
    Use this instead of direct logger calls when logging user data or API responses.
    """
    
    def __init__(self, logger_name: str):
        """
        Initialize secure logger.
        
        Args:
            logger_name: Name for the underlying logger
        """
        self.logger = get_logger(logger_name)
    
    def _sanitize_args(self, *args) -> tuple:
        """Sanitize all string arguments."""
        return tuple(
            SecretsManager.sanitize_string(arg) if isinstance(arg, str) else arg
            for arg in args
        )
    
    def _sanitize_kwargs(self, kwargs: dict) -> dict:
        """Sanitize dictionary arguments."""
        return SecretsManager.sanitize_dict(kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with sanitization."""
        sanitized_msg = SecretsManager.sanitize_string(msg)
        self.logger.debug(sanitized_msg, *self._sanitize_args(*args), **self._sanitize_kwargs(kwargs))
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message with sanitization."""
        sanitized_msg = SecretsManager.sanitize_string(msg)
        self.logger.info(sanitized_msg, *self._sanitize_args(*args), **self._sanitize_kwargs(kwargs))
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with sanitization."""
        sanitized_msg = SecretsManager.sanitize_string(msg)
        self.logger.warning(sanitized_msg, *self._sanitize_args(*args), **self._sanitize_kwargs(kwargs))
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message with sanitization."""
        sanitized_msg = SecretsManager.sanitize_string(msg)
        self.logger.error(sanitized_msg, *self._sanitize_args(*args), **self._sanitize_kwargs(kwargs))
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with sanitization."""
        sanitized_msg = SecretsManager.sanitize_string(msg)
        self.logger.critical(sanitized_msg, *self._sanitize_args(*args), **self._sanitize_kwargs(kwargs))


def get_secure_logger(name: str) -> SecureLogger:
    """
    Get a secure logger instance that automatically sanitizes sensitive data.
    
    Args:
        name: Logger name
        
    Returns:
        SecureLogger instance
    """
    return SecureLogger(name)


def perform_security_check() -> bool:
    """
    Perform comprehensive security check on application configuration.
    
    Returns:
        True if all security checks pass
    """
    print("\n" + "=" * 80)
    print("{lock} AI Video Agent - Security Check")
    print("=" * 80 + "\n")
    
    all_passed = True
    
    # Check secrets validation
    print(" Validating Secrets...")
    secrets_result = SecretsManager.validate_secrets()
    
    if secrets_result["missing"]:
        print(f"[wrong] Missing secrets: {', '.join(secrets_result['missing'])}")
        all_passed = False
    
    if secrets_result["invalid"]:
        print(f"[wrong] Invalid secrets: {', '.join(secrets_result['invalid'])}")
        all_passed = False
    
    if secrets_result["valid"]:
        print("[okay] All required secrets are properly configured")
    
    # Show warnings
    if secrets_result["warnings"]:
        print("\n[warning]  Security Warnings:")
        for warning in secrets_result["warnings"]:
            print(f"   {warning}")
        print()
    
    print("=" * 80)
    if all_passed and not secrets_result["warnings"]:
        print("[okay] Security Check Complete - No issues found")
    elif all_passed:
        print("[warning]  Security Check Complete - Review warnings above")
    else:
        print("[wrong] Security Check Failed - Fix issues above")
    print("=" * 80 + "\n")
    
    return all_passed
