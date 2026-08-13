"""
Tests for input validation module.
"""

import pytest
from core.validators import InputValidator
from core.exceptions import ValidationError


class TestURLValidation:
    """Test URL validation."""
    
    def test_valid_youtube_urls(self):
        """Test valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            validated = InputValidator.validate_url(url)
            assert validated == url
    
    def test_invalid_urls(self):
        """Test invalid URLs."""
        invalid_urls = [
            "not_a_url",
            "ftp://example.com",
            "https://google.com",  # Not YouTube
            "",
            None
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                InputValidator.validate_url(url)


class TestLanguageValidation:
    """Test language validation."""
    
    def test_valid_languages(self):
        """Test valid language inputs."""
        assert InputValidator.validate_language("english") == "english"
        assert InputValidator.validate_language("hinglish") == "hinglish"
        assert InputValidator.validate_language("ENGLISH") == "english"
        assert InputValidator.validate_language(" english ") == "english"
    
    def test_invalid_languages(self):
        """Test invalid language inputs."""
        with pytest.raises(ValidationError):
            InputValidator.validate_language("spanish")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_language("")
        
        with pytest.raises(ValidationError):
            InputValidator.validate_language(None)


class TestTranscriptValidation:
    """Test transcript validation."""
    
    def test_valid_transcript(self):
        """Test valid transcript."""
        transcript = "This is a valid transcript with enough content."
        validated = InputValidator.validate_transcript(transcript)
        assert validated == transcript
    
    def test_too_short_transcript(self):
        """Test transcript that's too short."""
        with pytest.raises(ValidationError):
            InputValidator.validate_transcript("short")
    
    def test_empty_transcript(self):
        """Test empty transcript."""
        with pytest.raises(ValidationError):
            InputValidator.validate_transcript("")


class TestQuestionValidation:
    """Test question validation."""
    
    def test_valid_question(self):
        """Test valid question."""
        question = "What were the main decisions?"
        validated = InputValidator.validate_question(question)
        assert validated == question
    
    def test_too_short_question(self):
        """Test question that's too short."""
        with pytest.raises(ValidationError):
            InputValidator.validate_question("Hi")
    
    def test_too_long_question(self):
        """Test question that's too long."""
        long_question = "x" * 1001
        with pytest.raises(ValidationError):
            InputValidator.validate_question(long_question)


class TestFilenameS anitization:
    """Test filename sanitization."""
    
    def test_sanitize_normal_filename(self):
        """Test sanitizing normal filename."""
        result = InputValidator.sanitize_filename("my_file.txt")
        assert result == "my_file.txt"
    
    def test_sanitize_dangerous_characters(self):
        """Test sanitizing dangerous characters."""
        result = InputValidator.sanitize_filename("file<>:\"\\|?*.txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
    
    def test_sanitize_empty_filename(self):
        """Test sanitizing empty filename."""
        result = InputValidator.sanitize_filename("")
        assert result == "unnamed_file"
