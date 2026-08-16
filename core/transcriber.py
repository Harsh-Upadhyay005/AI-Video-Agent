import whisper
import os
import requests
import torch
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def load_model():
    """Load Whisper model once and reuse it."""
    global _model
    if _model is None:
        print(f"[Whisper] Loading model: {WHISPER_MODEL}")
        _model = whisper.load_model(WHISPER_MODEL)
        print(f"[Whisper] Model loaded successfully.")
    return _model


def transcribe_chunk_whisper(chunk_path: str, progress_callback: Optional[Callable] = None, return_segments: bool = False):
    """
    Transcribe a single audio chunk using OpenAI Whisper.
    
    Args:
        chunk_path: Path to the audio chunk
        progress_callback: Optional callback for progress updates
        return_segments: If True, return segments with timestamps; if False, return text only
    
    Returns:
        If return_segments=False: Transcribed text string
        If return_segments=True: Dict with 'text' and 'segments' (list of {text, start, end})
    """
    model = load_model()
    
    if progress_callback:
        progress_callback("transcribing", os.path.basename(chunk_path))
    
    try:
        result = model.transcribe(chunk_path)
        
        if return_segments and "segments" in result:
            # Return structured data with timestamps
            return {
                "text": result["text"],
                "segments": [
                    {
                        "text": seg.get("text", ""),
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 0.0)
                    }
                    for seg in result.get("segments", [])
                ]
            }
        else:
            # Backward compatible: return text only
            return result["text"]
    except Exception as e:
        print(f"[Whisper] Error transcribing {chunk_path}: {e}")
        if return_segments:
            return {"text": "", "segments": []}
        return ""


def _send_to_sarvam(piece_path: str) -> str:
    """Send one ≤30s WAV file to Sarvam and return the English transcript."""
    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": SARVAM_MODEL, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\n Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str, progress_callback: Optional[Callable] = None) -> str:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            if progress_callback:
                progress_callback("transcribing_piece", f"piece {i + 1}/{total_pieces}")
            print(f"   Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english", progress_callback: Optional[Callable] = None) -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english   Whisper (local model)
    - hinglish  Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path, progress_callback)
    return transcribe_chunk_whisper(chunk_path, progress_callback)


def transcribe_all(
    chunks: list, 
    language: str = "english", 
    progress_callback: Optional[Callable] = None
) -> str:
    """
    Transcribe all audio chunks sequentially.
    
    Args:
        chunks: List of audio chunk file paths
        language: Language for transcription (english or hinglish)
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Complete transcript text
    """
    engine = "Sarvam AI" if language.lower() == "hinglish" else "OpenAI Whisper (small)"
    print(f"[Transcription] Using {engine} for transcription.")
    
    total_chunks = len(chunks)
    full_transcript = ""
    
    for i, chunk in enumerate(chunks):
        print(f"[Transcription] Transcribing chunk {i + 1}/{total_chunks}...")
        if progress_callback:
            progress_callback("transcribing_chunk", f"{i + 1}/{total_chunks}")
        
        text = transcribe_chunk(chunk, language=language, progress_callback=progress_callback)
        full_transcript += text + " "
    
    print("[Transcription] Transcription complete.")
    if progress_callback:
        progress_callback("transcription_complete", "All chunks processed")
    
    return full_transcript.strip()