"""
Tests for security utilities.
"""

import pytest
from core.security import SecretsManager


class TestSecretsManager:
    """Test secrets management."""
    
    def test_sanitize_api_key_in_string(self):
        """Test sanitizing API keys from strings."""
        text = "My API key is api_key=sk_test_1234567890"
        sanitized = SecretsManager.sanitize_string(text)
        
        assert "sk_test_1234567890" not in sanitized
        assert "REDACTED" in sanitized
    
    def test_sanitize_password_in_string(self):
        """Test sanitizing passwords from strings."""
        text = "password=mysecretpass123"
        sanitized = SecretsManager.sanitize_string(text)
        
        assert "mysecretpass123" not in sanitized
        assert "REDACTED" in sanitized
    
    def test_sanitize_dict_with_sensitive_keys(self):
        """Test sanitizing dictionaries."""
        data = {
            "username": "john",
            "api_key": "secret123",
            "password": "pass123",
            "email": "john@example.com"
        }
        
        sanitized = SecretsManager.sanitize_dict(data)
        
        assert sanitized["username"] == "john"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["password"] == "***REDACTED***"
    
    def test_mask_api_key(self):
        """Test API key masking."""
        key = "sk_test_1234567890abcdef"
        masked = SecretsManager.mask_api_key(key, visible_chars=4)
        
        assert masked.startswith("sk_t")
        assert masked.endswith("cdef")
        assert "..." in masked
        assert "1234567890" not in masked
    
    def test_validate_api_key_format(self):
        """Test API key format validation."""
        # Valid key
        assert SecretsManager.validate_api_key_format("sk_test_1234567890abcdef")
        
        # Too short
        assert not SecretsManager.validate_api_key_format("short")
        
        # Placeholder
        assert not SecretsManager.validate_api_key_format("your_api_key_here")
        
        # Empty
        assert not SecretsManager.validate_api_key_format("")


class TestSecureLogger:
    """Test secure logging."""
    
    def test_secure_logger_sanitizes_api_keys(self, caplog):
        """Test that secure logger sanitizes sensitive data."""
        from core.security import get_secure_logger
        
        logger = get_secure_logger(__name__)
        logger.info("API key is: api_key=sk_test_secret123")
        
        # Check that the sensitive data was sanitized in logs
        assert "sk_test_secret123" not in caplog.text
        assert "REDACTED" in caplog.text or "api_key" in caplog.text
