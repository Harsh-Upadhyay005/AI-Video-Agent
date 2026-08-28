"""
Speech-to-Text Service Abstraction.
Separates STT (audio → text) from LLM (text → reasoning).

This module handles audio transcription using configured STT providers:
- Whisper (local, open-source)
- Sarvam (API, Hindi/Hinglish support)
- Mistral (API, if they offer STT)

IMPORTANT: This is NOT the same as Mistral LLM.
STT converts speech to text.
LLM generates reasoning/answers from text.
"""

import os
from typing import List, Optional, Callable, Protocol
from abc import ABC, abstractmethod
from pathlib import Path

from core.logger import get_logger
from core.config import ConfigManager

logger = get_logger(__name__)


class STTProvider(Protocol):
    """Protocol for speech-to-text providers."""
    
    def transcribe(self, audio_path: str, language: str = "english") -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'english', 'hinglish')
            
        Returns:
            Transcribed text
        """
        ...


class WhisperSTTProvider:
    """
    Whisper-based STT provider (local, open-source).
    Uses OpenAI's Whisper model running locally.
    """
    
    def __init__(self, model: str = "small"):
        """
        Initialize Whisper STT provider.
        
        Args:
            model: Whisper model size (tiny, base, small, medium, large)
        """
        self.model = model
        self._whisper = None
        logger.info(f"[WhisperSTT] Initialized with model: {model}")
    
    def _load_whisper(self):
        """Lazy load Whisper model."""
        if self._whisper is None:
            try:
                import whisper
                logger.info(f"[WhisperSTT] Loading Whisper model: {self.model}")
                self._whisper = whisper.load_model(self.model)
                logger.info("[WhisperSTT] Model loaded successfully")
            except ImportError:
                raise ImportError(
                    "Whisper not installed. Install with: pip install openai-whisper"
                )
            except Exception as e:
                raise Exception(f"Failed to load Whisper model: {e}")
        return self._whisper
    
    def transcribe(self, audio_path: str, language: str = "english") -> str:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to audio file
            language: Language code (ignored for Whisper, auto-detects)
            
        Returns:
            Transcribed text
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"[WhisperSTT] Transcribing: {Path(audio_path).name}")
        
        model = self._load_whisper()
        
        try:
            result = model.transcribe(audio_path)
            text = result["text"].strip()
            
            logger.info(f"[WhisperSTT] Transcribed {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"[WhisperSTT] Transcription failed: {e}")
            raise Exception(f"Whisper transcription failed: {e}")


class SarvamSTTProvider:
    """
    Sarvam AI STT provider (API-based, Hindi/Hinglish support).
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Sarvam STT provider.
        
        Args:
            api_key: Sarvam API key (defaults to env SARVAM_API_KEY)
            model: Sarvam model (defaults to env SARVAM_STT_MODEL)
        """
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        self.model = model or os.getenv("SARVAM_STT_MODEL", "saaras:v3")
        
        if not self.api_key:
            raise ValueError(
                "SARVAM_API_KEY not found. Set it in .env file for Hindi/Hinglish support."
            )
        
        logger.info(f"[SarvamSTT] Initialized with model: {self.model}")
    
    def transcribe(self, audio_path: str, language: str = "hinglish") -> str:
        """
        Transcribe audio using Sarvam API.
        
        Args:
            audio_path: Path to audio file
            language: Language code ('hinglish' for Sarvam)
            
        Returns:
            Transcribed text
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"[SarvamSTT] Transcribing: {Path(audio_path).name}")
        
        try:
            import requests
            
            url = "https://api.sarvam.ai/speech-to-text"
            
            with open(audio_path, 'rb') as audio_file:
                files = {'file': audio_file}
                headers = {'api-subscription-key': self.api_key}
                data = {'model': self.model}
                
                response = requests.post(url, files=files, headers=headers, data=data)
                response.raise_for_status()
                
                result = response.json()
                text = result.get('transcript', '').strip()
                
                logger.info(f"[SarvamSTT] Transcribed {len(text)} characters")
                return text
                
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")
        except Exception as e:
            logger.error(f"[SarvamSTT] Transcription failed: {e}")
            raise Exception(f"Sarvam transcription failed: {e}")


class STTService:
    """
    Unified Speech-to-Text service.
    Routes to appropriate provider based on language and configuration.
    """
    
    def __init__(self):
        """Initialize STT service with configured providers."""
        try:
            from core.config import get_config
            self.config = get_config()
        except Exception:
            # If config not initialized, it's okay - providers will handle their own config
            self.config = None
        
        # Initialize providers
        self.whisper_provider = None
        self.sarvam_provider = None
        
        logger.info("[STTService] Initialized")
    
    def _get_whisper_provider(self) -> WhisperSTTProvider:
        """Lazy initialize Whisper provider."""
        if self.whisper_provider is None:
            model = os.getenv("WHISPER_MODEL", "small")
            self.whisper_provider = WhisperSTTProvider(model=model)
        return self.whisper_provider
    
    def _get_sarvam_provider(self) -> SarvamSTTProvider:
        """Lazy initialize Sarvam provider."""
        if self.sarvam_provider is None:
            self.sarvam_provider = SarvamSTTProvider()
        return self.sarvam_provider
    
    def transcribe(
        self, 
        audio_path: str, 
        language: str = "english",
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """
        Transcribe audio file to text using appropriate provider.
        
        Args:
            audio_path: Path to audio file
            language: Language ('english', 'hinglish', etc.)
            progress_callback: Optional callback(stage, message)
            
        Returns:
            Transcribed text
        """
        logger.info(f"[STTService] Transcribing audio: language={language}")
        
        if progress_callback:
            progress_callback("stt", f"Transcribing audio ({language})...")
        
        # Route to appropriate provider
        if language.lower() in ['hinglish', 'hindi']:
            # Use Sarvam for Hindi/Hinglish
            try:
                provider = self._get_sarvam_provider()
                text = provider.transcribe(audio_path, language)
                
                if progress_callback:
                    progress_callback("stt", "Transcription complete (Sarvam)")
                
                return text
                
            except Exception as e:
                logger.warning(f"[STTService] Sarvam failed, falling back to Whisper: {e}")
                # Fall back to Whisper
                provider = self._get_whisper_provider()
                text = provider.transcribe(audio_path, language)
                
                if progress_callback:
                    progress_callback("stt", "Transcription complete (Whisper fallback)")
                
                return text
        else:
            # Use Whisper for English and other languages
            provider = self._get_whisper_provider()
            text = provider.transcribe(audio_path, language)
            
            if progress_callback:
                progress_callback("stt", "Transcription complete (Whisper)")
            
            return text
    
    def transcribe_multiple(
        self,
        audio_paths: List[str],
        language: str = "english",
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """
        Transcribe multiple audio chunks and combine.
        
        Args:
            audio_paths: List of audio file paths
            language: Language for transcription
            progress_callback: Optional callback(stage, message)
            
        Returns:
            Combined transcript
        """
        logger.info(f"[STTService] Transcribing {len(audio_paths)} audio chunks")
        
        transcripts = []
        
        for i, audio_path in enumerate(audio_paths):
            if progress_callback:
                progress_callback(
                    "stt",
                    f"Transcribing chunk {i+1}/{len(audio_paths)}..."
                )
            
            try:
                text = self.transcribe(audio_path, language, progress_callback=None)
                transcripts.append(text)
                
            except Exception as e:
                logger.error(f"[STTService] Failed to transcribe chunk {i+1}: {e}")
                # Continue with other chunks
                continue
        
        combined_transcript = "\n\n".join(transcripts)
        
        logger.info(f"[STTService] Combined transcript: {len(combined_transcript)} characters")
        
        if progress_callback:
            progress_callback("stt", f"Transcription complete ({len(audio_paths)} chunks)")
        
        return combined_transcript


# Singleton instance
_stt_service_instance = None


def get_stt_service() -> STTService:
    """
    Get singleton STT service instance.
    
    Returns:
        STTService instance
    """
    global _stt_service_instance
    
    if _stt_service_instance is None:
        _stt_service_instance = STTService()
    
    return _stt_service_instance
