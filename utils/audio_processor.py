import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import yt_dlp
from pydub import AudioSegment

from core.logger import get_logger

logger = get_logger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _find_browser_executable(browser_name: str) -> Optional[str]:
    """
    Find browser executable on Windows by checking common installation paths.
    shutil.which() doesn't work because browsers aren't in PATH on Windows.
    """
    # Define Windows-specific paths for each browser
    browser_paths = {
        "chrome": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ],
        "edge": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ],
        "firefox": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Mozilla Firefox" / "firefox.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Mozilla Firefox" / "firefox.exe",
        ],
        "brave": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
        ],
        "opera": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Opera" / "opera.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Opera" / "opera.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Opera" / "opera.exe",
        ],
    }
    
    # Check each path for this browser
    for path in browser_paths.get(browser_name.lower(), []):
        if path.exists():
            logger.info(f"✓ Found {browser_name} at: {path}")
            return str(path)
    
    return None


def _build_yt_dlp_options(output_path: str, node_path: str, client: str = "android") -> dict:
    """
    Build yt-dlp options with proper cookie-based authentication.
    
    YouTube now REQUIRES browser cookies (OAuth is deprecated).
    This function extracts cookies from installed browsers automatically.
    """
    # Try to extract cookies from browsers - THIS IS NOW REQUIRED, NOT OPTIONAL
    # Priority order: Chrome > Edge > Firefox > Brave > Opera
    cookiesfrombrowser = None
    available_browsers = []
    
    # Check which browsers are available using Windows-specific paths
    browser_candidates = [
        ("chrome", "Chrome"),
        ("edge", "Edge"),
        ("firefox", "Firefox"),
        ("brave", "Brave"),
        ("opera", "Opera"),
    ]
    
    for browser_name, display_name in browser_candidates:
        browser_path = _find_browser_executable(browser_name)
        if browser_path:
            available_browsers.append(display_name)
            if cookiesfrombrowser is None:  # Use first found
                cookiesfrombrowser = (browser_name, display_name)
                logger.info(f"✓ Will extract cookies from {display_name}")
    
    if not cookiesfrombrowser:
        logger.warning("⚠ No browser found for cookie extraction!")
        logger.warning("Checked: Chrome, Edge, Firefox, Brave, Opera")
        logger.warning("YouTube downloads may fail without browser cookies!")
    
    # Enhanced options for YouTube with cookie authentication
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "restrictfilenames": True,
        "noplaylist": True,
        "no_warnings": False,  # Show warnings
        "quiet": False,  # Show output for debugging
        "verbose": False,
        
        # Node.js for signature deciphering
        "js_runtimes": {"node": {"executable": node_path}},
        
        # Client strategy
        "extractor_args": {
            "youtube": {
                "player_client": [client],
                "player_skip": ["webpage", "configs"],
                "skip": ["hls", "dash"],
            }
        },
        
        # Updated headers
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        },
        
        # FFmpeg post-processing
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        
        # Retry settings
        "retries": 3,
        "fragment_retries": 3,
        "skip_unavailable_fragments": True,
        "ignoreerrors": False,
    }
    
    # Add browser cookies - CRITICAL for YouTube
    if cookiesfrombrowser:
        browser_name, display_name = cookiesfrombrowser
        options["cookiesfrombrowser"] = (browser_name,)
        logger.info(f"✓ Using cookies from {display_name}")
        logger.warning(f"  IMPORTANT: {display_name} MUST be closed for cookie extraction!")
    else:
        logger.error("✗ NO BROWSER FOUND for cookie extraction!")
        logger.error("  YouTube downloads will likely FAIL without cookies")
        logger.error("  Install Chrome, Edge, or Firefox to enable cookie extraction")
    
    return options


def download_youtube_audio(url: str) -> str:
    """
    Download audio from YouTube URL with cookie-based authentication.
    
    YouTube now REQUIRES browser cookies (OAuth is deprecated).
    Make sure you're logged into YouTube in Chrome, Edge, or Firefox.
    
    IMPORTANT: Close your browser before running downloads, or cookies cannot be extracted!
    
    Args:
        url: YouTube URL
        
    Returns:
        Path to downloaded WAV file
        
    Raises:
        RuntimeError: If all download strategies fail
    """
    logger.info(f"Attempting to download YouTube audio: {url}")
    
    # Check Node.js availability
    if shutil.which("node") is None:
        error_msg = (
            "Node.js is required for YouTube downloads. "
            "Install Node.js from https://nodejs.org/ and ensure 'node' is in your PATH."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    node_path = shutil.which("node") or "node"
    last_error = None
    
    # Check available browsers for cookie extraction using Windows paths
    available_browsers = []
    browser_candidates = [("chrome", "Chrome"), ("edge", "Edge"), ("firefox", "Firefox"), 
                         ("brave", "Brave"), ("opera", "Opera")]
    
    for browser_name, display_name in browser_candidates:
        if _find_browser_executable(browser_name):
            available_browsers.append(display_name)
    
    if not available_browsers:
        error_msg = (
            "❌ NO BROWSER FOUND for YouTube cookie extraction!\n\n"
            "YouTube now REQUIRES browser cookies for downloads.\n"
            "OAuth authentication is no longer supported.\n\n"
            "PLEASE INSTALL one of these browsers:\n"
            "• Google Chrome (recommended)\n"
            "• Microsoft Edge\n"
            "• Firefox\n"
            "• Brave\n"
            "• Opera\n\n"
            "After installing a browser:\n"
            "1. Login to YouTube in the browser\n"
            "2. Try the download again\n\n"
            "Alternative: Upload the MP3/MP4 file directly instead of using YouTube URL"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"✓ Found browsers: {', '.join(available_browsers)}")
    logger.warning(f"⚠️ IMPORTANT: CLOSE {available_browsers[0]} before downloading!")
    logger.warning(f"   (yt-dlp cannot extract cookies while browser is running)")
    
    # Try multiple client strategies in order of success rate
    client_strategies = [
        ("web", "Web client (most compatible)"),
        ("android", "Android client"),
        ("ios", "iOS client"),
        ("tv_embedded", "TV embedded client"),
        ("mweb", "Mobile web client"),
    ]
    
    for attempt, (client, description) in enumerate(client_strategies, 1):
        try:
            logger.info(f"Attempt {attempt}/{len(client_strategies)}: Trying {description}...")
            
            ydl_opts = _build_yt_dlp_options(output_path, node_path, client=client)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Extracting video info...")
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    raise yt_dlp.utils.DownloadError("No video metadata returned for YouTube URL")
                
                filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".wav"
                logger.info(f"✓ Successfully downloaded: {filename}")
                return filename
                
        except yt_dlp.utils.DownloadError as e:
            last_error = e
            error_str = str(e)
            
            # Check for the Chrome cookie database lock error
            if "Could not copy Chrome cookie database" in error_str or "7271" in error_str:
                logger.error(f"  ✗ Chrome is RUNNING - cannot extract cookies!")
                logger.error(f"     Close Chrome and try again, OR login to Edge/Firefox instead")
                # Don't continue - all attempts will fail with same error
                raise RuntimeError(
                    f"❌ Cannot extract cookies from Chrome because it's RUNNING\n\n"
                    f"FIX Option 1 (RECOMMENDED):\n"
                    f"1. CLOSE Chrome completely (all windows)\n"
                    f"2. Wait 5 seconds\n"
                    f"3. Try the download again\n\n"
                    f"FIX Option 2:\n"
                    f"1. Open Edge or Firefox\n"
                    f"2. Login to YouTube there\n"
                    f"3. Close Edge/Firefox\n"
                    f"4. Uninstall or rename Chrome temporarily\n"
                    f"5. Try the download again (will use Edge/Firefox)\n\n"
                    f"FIX Option 3:\n"
                    f"• Download the video manually and upload the MP3/MP4 file\n\n"
                    f"Technical details: yt-dlp cannot access Chrome's cookie database\n"
                    f"while Chrome is running because the database is locked.\n"
                    f"See: https://github.com/yt-dlp/yt-dlp/issues/7271"
                ) from e
            
            # Log the specific error
            if "Login with OAuth is no longer supported" in error_str:
                logger.warning(f"  ✗ OAuth deprecated - need browser cookies")
            elif "403" in error_str or "Forbidden" in error_str:
                logger.warning(f"  ✗ 403 Forbidden with {client} client")
            elif "429" in error_str:
                logger.warning(f"  ✗ Rate limited (429) - adding delay...")
                import time
                time.sleep(5)
            elif "Private video" in error_str or "members-only" in error_str:
                logger.error(f"  ✗ Video is private or members-only")
                raise RuntimeError(
                    "This video is private, members-only, or requires login. "
                    "The system cannot access it. Please use a public video."
                )
            elif "Video unavailable" in error_str:
                logger.error(f"  ✗ Video unavailable (deleted, region-locked, or invalid URL)")
                raise RuntimeError(
                    "This video is unavailable (deleted, region-locked, or invalid URL). "
                    "Please check the URL and try a different video."
                )
            else:
                logger.warning(f"  ✗ {client} failed: {error_str}")
            
            continue
            
        except Exception as exc:
            last_error = exc
            logger.warning(f"  ✗ Unexpected error with {client}: {exc}")
            continue
    
    # All strategies failed
    error_msg = (
        f"Unable to download YouTube audio after trying {len(client_strategies)} strategies.\n\n"
        f"Last error: {last_error}\n\n"
        f"⚠️ CRITICAL: YouTube now REQUIRES browser cookies for downloads.\n"
        f"OAuth authentication is NO LONGER SUPPORTED by YouTube.\n\n"
        f"REQUIRED STEPS TO FIX:\n"
        f"1. Login to YouTube in {available_browsers[0]}\n"
        f"2. CLOSE {available_browsers[0]} completely (all windows)\n"
        f"3. Wait 5 seconds for browser to fully close\n"
        f"4. Try the download again\n\n"
        f"WHY: yt-dlp cannot extract cookies while the browser is running.\n"
        f"The browser locks its cookie database.\n\n"
        f"Detected browsers: {', '.join(available_browsers)}\n"
        f"Will try to use: {available_browsers[0]}\n\n"
        f"Still failing? Check these:\n"
        f"• Make sure browser is actually CLOSED (check Task Manager)\n"
        f"• Try using Edge or Firefox instead of Chrome\n"
        f"• Update yt-dlp: pip install --upgrade yt-dlp\n"
        f"• Video might be private, age-restricted, or region-locked\n\n"
        f"Alternative solution:\n"
        f"• Download the video manually and upload the MP3/MP4 file\n\n"
        f"Help: docs/YOUTUBE_DOWNLOAD_TROUBLESHOOTING.md"
    )
    
    logger.error(error_msg)
    raise RuntimeError(error_msg) from last_error


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to WAV format using FFmpeg directly.
    Handles both audio and video files, extracting audio from video.
    """
    logger.info(f"Converting file to WAV: {input_path}")
    
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Output path in same directory
    output_path = input_path_obj.parent / f"{input_path_obj.stem}_converted.wav"
    
    try:
        # Use FFmpeg for robust conversion
        # Extract audio, convert to mono, 16kHz sample rate
        command = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # PCM 16-bit
            "-ar", "16000",  # 16kHz sample rate
            "-ac", "1",  # Mono
            "-y",  # Overwrite output
            str(output_path)
        ]
        
        logger.info(f"Running FFmpeg: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
        
        if not output_path.exists():
            raise RuntimeError("FFmpeg conversion completed but output file not found")
        
        logger.info(f"Conversion successful: {output_path}")
        return str(output_path)
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timed out")
        raise RuntimeError("File conversion timed out (maximum 5 minutes)")
    except FileNotFoundError:
        logger.error("FFmpeg not found in PATH")
        raise RuntimeError(
            "FFmpeg not installed. Please install FFmpeg and ensure it's in your PATH. "
            "Windows: Download from https://ffmpeg.org/download.html"
        )
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to convert file: {str(e)}")

def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """
    Split audio file into chunks of specified duration.
    
    Args:
        wav_path: Path to WAV file
        chunk_minutes: Duration of each chunk in minutes
        
    Returns:
        List of chunk file paths
    """
    logger.info(f"Chunking audio: {wav_path} ({chunk_minutes} min chunks)")
    
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    
    chunks = []
    total_duration = len(audio) / 1000 / 60  # minutes
    
    logger.info(f"Audio duration: {total_duration:.2f} minutes")
    
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
        
        chunk_duration = len(chunk) / 1000 / 60
        logger.info(f"Created chunk {i + 1}: {chunk_duration:.2f} minutes")
    
    logger.info(f"Created {len(chunks)} chunk(s)")
    return chunks

def process_input(source: str) -> list:
    """
    Unified media processing pipeline.
    Handles YouTube URLs, local audio files, and local video files.
    
    Args:
        source: YouTube URL or local file path
        
    Returns:
        List of audio chunk file paths
    """
    logger.info(f"Processing input: {source}")
    
    # Determine source type and process accordingly
    if source.startswith("http://") or source.startswith("https://"):
        logger.info("Detected YouTube URL - downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        logger.info("Detected local file - converting to WAV...")
        
        # Check if file exists
        if not Path(source).exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        # Convert to WAV (works for both audio and video)
        wav_path = convert_to_wav(source)
    
    logger.info("Chunking audio...")
    chunks = chunk_audio(wav_path)
    
    logger.info(f"✓ Audio processing complete - {len(chunks)} chunk(s) created")
    return chunks

