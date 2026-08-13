import whisper
import os
import requests
import torch
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25


# Auto-detect device: CUDA if available, else CPU
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", DEVICE)  # Allow .env override, but default to auto-detect
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def load_model():
    global _model  
    if _model is None:
        device_info = f"{WHISPER_DEVICE.upper()}"
        if WHISPER_DEVICE == "cuda":
            device_info += f" (GPU: {torch.cuda.get_device_name(0)})"
        
        print(f"Loading Whisper model: {WHISPER_MODEL} on {device_info}...")
        _model = whisper.load_model(WHISPER_MODEL, device=WHISPER_DEVICE)
        print("✅ Whisper model loaded.")
        
        if WHISPER_DEVICE == "cuda":
            print(f"⚡ GPU acceleration enabled! Transcription will be 10-50x faster.")
    return _model 


def transcribe_chunk_whisper(chunk_path: str, progress_callback: Optional[Callable] = None) -> str:
    """
    Transcribe a single audio chunk using Whisper.
    
    Args:
        chunk_path: Path to the audio chunk
        progress_callback: Optional callback for progress updates
    
    Returns:
        Transcribed text
    """
    model = load_model()
    
    if progress_callback:
        progress_callback("transcribing", os.path.basename(chunk_path))
    
    # Optimize settings based on device
    fp16 = (WHISPER_DEVICE == "cuda")  # Use FP16 only on GPU
    
    result = model.transcribe(
        chunk_path, 
        task="transcribe",
        fp16=fp16,  # FP16 for CUDA, FP32 for CPU
        language=None,  # Auto-detect
        verbose=False  # Suppress output
    )
    
    return result["text"]


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
        print(f"\n❌ Sarvam returned {response.status_code}")
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
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english", progress_callback: Optional[Callable] = None) -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  → Whisper (local model)
    - hinglish → Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path, progress_callback)
    return transcribe_chunk_whisper(chunk_path, progress_callback)


def transcribe_all(
    chunks: list, 
    language: str = "english", 
    progress_callback: Optional[Callable] = None,
    parallel: bool = True,
    max_workers: int = 2
) -> str:
    """
    Transcribe all audio chunks with optional parallel processing.
    
    Args:
        chunks: List of audio chunk file paths
        language: Language for transcription (english or hinglish)
        progress_callback: Optional callback function for progress updates
        parallel: Whether to process chunks in parallel (faster)
        max_workers: Number of parallel workers (default: 2)
    
    Returns:
        Complete transcript text
    """
    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")
    
    total_chunks = len(chunks)
    
    if progress_callback:
        progress_callback("transcription_started", f"Processing {total_chunks} chunks with {engine}")
    
    # For Sarvam (API-based), process sequentially to avoid rate limits
    # For Whisper (local), can process in parallel
    if language.lower() == "hinglish" or not parallel:
        # Sequential processing
        full_transcript = ""
        for i, chunk in enumerate(chunks):
            print(f"Transcribing chunk {i + 1}/{total_chunks}...")
            if progress_callback:
                progress_callback("transcribing_chunk", f"{i + 1}/{total_chunks}")
            
            text = transcribe_chunk(chunk, language=language, progress_callback=progress_callback)
            full_transcript += text + " "
    else:
        # Parallel processing for Whisper (faster!)
        full_transcript = ""
        transcripts = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks for processing
            future_to_chunk = {
                executor.submit(transcribe_chunk, chunk, language, progress_callback): (i, chunk)
                for i, chunk in enumerate(chunks)
            }
            
            # Process results as they complete
            completed = 0
            for future in as_completed(future_to_chunk):
                chunk_idx, chunk_path = future_to_chunk[future]
                completed += 1
                
                print(f"Completed chunk {completed}/{total_chunks}")
                if progress_callback:
                    progress_callback("chunk_completed", f"{completed}/{total_chunks}")
                
                try:
                    text = future.result()
                    transcripts[chunk_idx] = text
                except Exception as e:
                    print(f"Error transcribing chunk {chunk_idx}: {e}")
                    transcripts[chunk_idx] = ""
        
        # Combine transcripts in order
        for i in range(len(chunks)):
            full_transcript += transcripts.get(i, "") + " "
    
    print("Transcription complete.")
    if progress_callback:
        progress_callback("transcription_complete", "All chunks processed")
    
    return full_transcript.strip()