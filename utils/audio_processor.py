import os
import shutil

import yt_dlp
from pydub import AudioSegment


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _build_yt_dlp_options(output_path: str, node_path: str, client: str = "android") -> dict:
    cookiesfrombrowser = []
    for browser in ("chrome", "msedge", "edge", "firefox", "brave"):
        if shutil.which(browser):
            cookiesfrombrowser.append(browser)
            break

    return {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "restrictfilenames": True,
        "js_runtimes": {"node": {"executable": node_path}},
        "extractor_args": {
            "youtube": [
                f"player_client={client}",
                "player_skip=webpage",
            ]
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "*/*",
        },
        "noplaylist": True,
        "no_warnings": True,
        "quiet": True,
        **({"cookiesfrombrowser": cookiesfrombrowser} if cookiesfrombrowser else {}),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }


def download_youtube_audio(url: str) -> str:
    if shutil.which("node") is None:
        raise RuntimeError(
            "Node.js is required for YouTube downloads. Install Node.js and ensure 'node' is on PATH."
        )

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    node_path = shutil.which("node") or "node"
    last_error = None

    for client in ("android", "ios", "tv_embedded"):
        try:
            ydl_opts = _build_yt_dlp_options(output_path, node_path, client=client)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise yt_dlp.utils.DownloadError("No video metadata returned for YouTube URL")
                filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".wav"
            return filename
        except Exception as exc:  # pragma: no cover - exercised by real YouTube retries
            last_error = exc

    raise RuntimeError(
        "Unable to download YouTube audio after retrying multiple client strategies. "
        f"Last error: {last_error}"
    ) from last_error


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path

def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks

