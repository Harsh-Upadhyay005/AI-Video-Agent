"""
Pytest configuration and fixtures.
"""

import pytest
import os
from pathlib import Path
from core.config import ConfigManager


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["MISTRAL_API_KEY"] = "test_mistral_key_1234567890"
    os.environ["WHISPER_MODEL"] = "tiny"  # Use smallest model for tests
    yield
    # Cleanup
    ConfigManager.reset()


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for tests."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return """
    This is a sample meeting transcript for testing purposes.
    We discussed the project roadmap and assigned action items.
    John will handle the backend development.
    Sarah will work on the frontend.
    The deadline is set for next Friday.
    """


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    from core.config import AppConfig, AudioConfig, WhisperConfig, MistralConfig, VectorStoreConfig, LoggingConfig
    
    return AppConfig(
        environment="development",
        debug=True,
        audio=AudioConfig(download_dir="test_downloads"),
        whisper=WhisperConfig(model_name="tiny"),
        mistral=MistralConfig(api_key="test_key"),
        vector_store=VectorStoreConfig(persist_directory="test_vector_db"),
        logging=LoggingConfig(log_dir="test_logs")
    )
