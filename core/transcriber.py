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

# Global model cache
_faster_model = None
_legacy_model = None
_engine_type = None


def load_model():
    """Load fastest available Whisper model once and reuse it."""
    global _faster_model, _legacy_model, _engine_type
    
    if _faster_model is not None:
        return _faster_model
    if _legacy_model is not None:
        return _legacy_model
        
    device = os.getenv("WHISPER_DEVICE", "auto").lower()
    if device == "auto":
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
            
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8") if device == "cpu" else "float16"
    threads = min(4, os.cpu_count() or 4)

    try:
        from faster_whisper import WhisperModel
        print(f"[Whisper] Loading faster-whisper model: {WHISPER_MODEL} ({device}, {compute_type})")
        _faster_model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute_type, cpu_threads=threads)
        _engine_type = "faster-whisper"
        print("[Whisper] faster-whisper loaded successfully.")
        return _faster_model
    except Exception as e:
        print(f"[Whisper] faster-whisper not available ({e}), falling back to standard Whisper...")

    try:
        print(f"[Whisper] Loading standard Whisper model: {WHISPER_MODEL}")
        _legacy_model = whisper.load_model(WHISPER_MODEL, device=device)
        _engine_type = "whisper"
        print("[Whisper] Model loaded successfully.")
        return _legacy_model
    except Exception as e:
        print(f"[Whisper] Failed to load Whisper: {e}")
        raise


def transcribe_chunk_whisper(chunk_path: str, progress_callback: Optional[Callable] = None, return_segments: bool = False):
    """
    Transcribe a single audio chunk using high-performance faster-whisper or OpenAI Whisper.
    """
    model = load_model()
    
    if progress_callback:
        progress_callback("transcribing", os.path.basename(chunk_path))
    
    try:
        if _engine_type == "faster-whisper":
            segments, info = model.transcribe(
                chunk_path,
                beam_size=1,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                language="en"
            )
            seg_list = list(segments)
            full_text = " ".join(s.text for s in seg_list).strip()
            
            if return_segments:
                return {
                    "text": full_text,
                    "segments": [
                        {"text": s.text, "start": s.start, "end": s.end}
                        for s in seg_list
                    ]
                }
            return full_text
        else:
            options = {"fp16": False} if getattr(model, "device", None) == "cpu" else {}
            result = model.transcribe(chunk_path, **options)
            
            if return_segments and "segments" in result:
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
            return result["text"]
    except Exception as e:
        print(f"[Whisper] Error transcribing {chunk_path}: {e}")
        if return_segments:
            return {"text": "", "segments": []}
        return ""


def _send_to_sarvam(piece_path: str) -> str:
    """Send one <=30s WAV file to Sarvam and return the English transcript."""
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
    Sarvam sync API accepts <=30s audio. We split this chunk into
    25-second pieces, send in parallel using a thread pool, and join the transcripts.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    total_pieces = (len(audio) + piece_ms - 1) // piece_ms
    pieces = [audio[start: start + piece_ms] for start in range(0, len(audio), piece_ms)]

    def process_piece(index: int, piece_data) -> tuple[int, str]:
        piece_path = f"{chunk_path}_sv_{index}.wav"
        piece_data.export(piece_path, format="wav")
        try:
            transcript = _send_to_sarvam(piece_path)
            return index, transcript
        finally:
            if os.path.exists(piece_path):
                try:
                    os.remove(piece_path)
                except Exception:
                    pass

    # Process pieces concurrently (up to 5 workers for optimal speed)
    max_workers = min(5, max(1, total_pieces))
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_piece, i, piece): i for i, piece in enumerate(pieces)}
        for future in as_completed(futures):
            try:
                idx, text = future.result()
                results[idx] = text
                if progress_callback:
                    progress_callback("transcribing_piece", f"piece {len(results)}/{total_pieces}")
            except Exception as e:
                idx = futures[future]
                print(f"[Sarvam] Piece {idx + 1} failed: {e}")
                results[idx] = ""

    full_text = " ".join(results.get(i, "") for i in range(total_pieces))
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
    Transcribe all audio chunks with parallel processing for Whisper.
    
    Optimizations:
    - Pre-loads model before parallel execution to avoid lock contention
    - Uses ThreadPoolExecutor for concurrent chunk transcription (Whisper)
    - Falls back to sequential for Sarvam (already parallelized internally)
    
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
    
    # Single chunk — skip parallelism overhead
    if total_chunks <= 1:
        if progress_callback:
            progress_callback("transcribing_chunk", "1/1")
        text = transcribe_chunk(chunks[0], language=language, progress_callback=progress_callback) if chunks else ""
        if progress_callback:
            progress_callback("transcription_complete", "All chunks processed")
        return text.strip()
    
    # Pre-load model BEFORE threading to avoid contention
    if language.lower() != "hinglish":
        load_model()
    
    # For Whisper (local model), transcribe in parallel threads
    # Sarvam already parallelizes internally, so keep it sequential
    use_parallel = language.lower() != "hinglish"
    
    if use_parallel:
        import threading
        completed = [0]
        lock = threading.Lock()
        results = {}
        
        def _transcribe_indexed(idx, chunk_path):
            text = transcribe_chunk(chunk_path, language=language, progress_callback=None)
            with lock:
                results[idx] = text
                completed[0] += 1
                if progress_callback:
                    progress_callback("transcribing_chunk", f"{completed[0]}/{total_chunks}")
        
        max_workers = min(3, total_chunks)  # Cap at 3 to avoid memory pressure
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_transcribe_indexed, i, chunk)
                for i, chunk in enumerate(chunks)
            ]
            for future in as_completed(futures):
                future.result()  # Propagate any exceptions
        
        # Reassemble in original order
        full_transcript = " ".join(results.get(i, "") for i in range(total_chunks))
    else:
        # Sequential for Sarvam
        parts = []
        for i, chunk in enumerate(chunks):
            print(f"[Transcription] Transcribing chunk {i + 1}/{total_chunks}...")
            if progress_callback:
                progress_callback("transcribing_chunk", f"{i + 1}/{total_chunks}")
            text = transcribe_chunk(chunk, language=language, progress_callback=progress_callback)
            parts.append(text)
        full_transcript = " ".join(parts)
    
    print("[Transcription] Transcription complete.")
    if progress_callback:
        progress_callback("transcription_complete", "All chunks processed")
    
    return full_transcript.strip()