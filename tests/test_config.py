"""
Tests for configuration management.
"""

import pytest
import os
from core.config import ConfigManager, AppConfig
from core.exceptions import ConfigurationError


class TestConfigManager:
    """Test configuration manager."""
    
    def test_initialize_config(self, setup_test_environment):
        """Test configuration initialization."""
        config = ConfigManager.initialize()
        
        assert config is not None
        assert isinstance(config, AppConfig)
        assert config.environment in ["development", "staging", "production"]
    
    def test_config_singleton(self, setup_test_environment):
        """Test that ConfigManager returns the same instance."""
        config1 = ConfigManager.get_config()
        config2 = ConfigManager.get_config()
        
        assert config1 is config2
    
    def test_missing_required_env_var(self):
        """Test error when required env var is missing."""
        # Remove required env var
        original = os.environ.get("MISTRAL_API_KEY")
        if "MISTRAL_API_KEY" in os.environ:
            del os.environ["MISTRAL_API_KEY"]
        
        ConfigManager.reset()
        
        with pytest.raises(ConfigurationError):
            ConfigManager.initialize()
        
        # Restore
        if original:
            os.environ["MISTRAL_API_KEY"] = original
    
    def test_config_reset(self, setup_test_environment):
        """Test configuration reset."""
        ConfigManager.initialize()
        ConfigManager.reset()
        
        # Should raise error if not initialized
        with pytest.raises(ConfigurationError):
            ConfigManager.get_config()


class TestEnvironmentValidation:
    """Test environment-specific configuration."""
    
    def test_production_mode(self):
        """Test production mode configuration."""
        os.environ["ENVIRONMENT"] = "production"
        ConfigManager.reset()
        config = ConfigManager.initialize()
        
        assert config.is_production()
        assert not config.is_development()
        assert config.debug == False
    
    def test_development_mode(self):
        """Test development mode configuration."""
        os.environ["ENVIRONMENT"] = "development"
        ConfigManager.reset()
        config = ConfigManager.initialize()
        
        assert config.is_development()
        assert not config.is_production()
