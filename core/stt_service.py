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
    Whisper-based STT provider (local, high performance).
    Uses faster-whisper (CTranslate2) with int8 quantization and VAD filtering,
    falling back to OpenAI's Whisper if faster-whisper is unavailable.
    """
    
    def __init__(self, model: str = "small"):
        """
        Initialize Whisper STT provider.
        
        Args:
            model: Whisper model size (tiny, base, small, medium, large)
        """
        self.model = model
        self._faster_model = None
        self._legacy_whisper = None
        self._engine = None
        logger.info(f"[WhisperSTT] Initialized with model: {model}")
    
    def _load_model(self):
        """Lazy load high-performance faster-whisper or fallback model."""
        if self._faster_model is not None or self._legacy_whisper is not None:
            return
            
        device = os.getenv("WHISPER_DEVICE", "auto").lower()
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8") if device == "cpu" else "float16"
        threads = min(4, os.cpu_count() or 4)

        # 1. Try faster-whisper (4x-8x faster CTranslate2 engine)
        try:
            from faster_whisper import WhisperModel
            logger.info(
                f"[WhisperSTT] Loading faster-whisper model: {self.model} "
                f"(device={device}, compute_type={compute_type}, threads={threads})"
            )
            self._faster_model = WhisperModel(
                self.model,
                device=device,
                compute_type=compute_type,
                cpu_threads=threads
            )
            self._engine = "faster-whisper"
            logger.info("[WhisperSTT] faster-whisper model loaded successfully")
            return
        except ImportError:
            logger.warning("[WhisperSTT] faster-whisper not installed; falling back to openai-whisper")
        except Exception as e:
            logger.warning(f"[WhisperSTT] faster-whisper initialization failed: {e}; falling back to openai-whisper")

        # 2. Fallback to standard OpenAI Whisper
        try:
            import whisper
            logger.info(f"[WhisperSTT] Loading standard Whisper model: {self.model} on {device}")
            self._legacy_whisper = whisper.load_model(self.model, device=device)
            self._engine = "whisper"
            logger.info("[WhisperSTT] Standard Whisper model loaded successfully")
        except ImportError:
            raise ImportError(
                "Neither faster-whisper nor openai-whisper is installed. "
                "Install with: pip install faster-whisper"
            )
        except Exception as e:
            raise Exception(f"Failed to load Whisper model: {e}")
    
    def transcribe(self, audio_path: str, language: str = "english") -> str:
        """
        Transcribe audio using the fastest available Whisper engine.
        
        Args:
            audio_path: Path to audio file
            language: Language code ('english', 'hinglish', or auto-detect)
            
        Returns:
            Transcribed text
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"[WhisperSTT] Transcribing: {Path(audio_path).name}")
        self._load_model()
        
        lang_code = "en" if language.lower() == "english" else None

        try:
            if self._engine == "faster-whisper" and self._faster_model is not None:
                # Use faster-whisper with VAD filter to strip silent audio chunks
                segments, info = self._faster_model.transcribe(
                    audio_path,
                    beam_size=1,  # Greedy decoding: 2x faster with minimal accuracy change
                    vad_filter=True,  # Filter out silence before transcription
                    vad_parameters=dict(min_silence_duration_ms=500),
                    language=lang_code
                )
                text = " ".join(seg.text for seg in segments).strip()
            else:
                # Legacy openai-whisper
                options = {"fp16": False} if getattr(self._legacy_whisper, "device", None) == "cpu" else {}
                if lang_code:
                    options["language"] = lang_code
                result = self._legacy_whisper.transcribe(audio_path, **options)
                text = result["text"].strip()
            
            logger.info(f"[WhisperSTT] Transcribed {len(text)} characters ({self._engine})")
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
        Transcribe multiple audio chunks with parallel processing.
        
        Optimizations:
        - Pre-loads Whisper model before spawning threads
        - Uses ThreadPoolExecutor (up to 3 workers) for concurrent transcription
        - Falls back to sequential for non-Whisper providers
        
        Args:
            audio_paths: List of audio file paths
            language: Language for transcription
            progress_callback: Optional callback(stage, message)
            
        Returns:
            Combined transcript
        """
        if not audio_paths:
            return ""
            
        if len(audio_paths) == 1:
            return self.transcribe(audio_paths[0], language, progress_callback)

        total = len(audio_paths)
        logger.info(f"[STTService] Transcribing {total} audio chunks")
        
        # Pre-load Whisper model before parallel execution
        use_whisper = language.lower() not in ['hinglish', 'hindi']
        if use_whisper:
            provider = self._get_whisper_provider()
            provider._load_model()  # Ensure model is loaded before threads start
        
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        completed_count = [0]
        lock = threading.Lock()
        results = {}
        
        def _transcribe_indexed(idx: int, path: str):
            text = self.transcribe(path, language, progress_callback=None)
            with lock:
                results[idx] = text
                completed_count[0] += 1
                if progress_callback:
                    progress_callback("stt", f"Transcribing chunk {completed_count[0]}/{total}...")
        
        max_workers = min(3, total)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_transcribe_indexed, i, path)
                for i, path in enumerate(audio_paths)
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"[STTService] Chunk transcription failed: {e}")
        
        # Reassemble in original order
        transcripts = [results[i] for i in range(total) if i in results and results[i]]
        
        combined_transcript = "\n\n".join(transcripts)
        logger.info(f"[STTService] Combined transcript: {len(combined_transcript)} characters")
        
        if progress_callback:
            progress_callback("stt", f"Transcription complete ({total} chunks)")
        
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
