"""Test YouTube download with cookie extraction"""
import sys
from utils.audio_processor import download_youtube_audio

def test_youtube_download():
    """Test downloading from YouTube with browser cookies"""
    
    # Use a known public, short video (YouTube's first video "Me at the zoo")
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    print("=" * 60)
    print("YOUTUBE DOWNLOAD TEST")
    print("=" * 60)
    print(f"Test URL: {test_url}")
    print(f"Video: 'Me at the zoo' (YouTube's first video - 18 seconds)")
    print("=" * 60)
    print()
    
    try:
        print("Starting download...")
        print("(This will test browser cookie extraction)")
        print()
        
        result = download_youtube_audio(test_url)
        
        print()
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"Downloaded file: {result}")
        print()
        print("YouTube download is working correctly!")
        print("Browser cookie extraction is functioning.")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting steps:")
        print("1. Make sure you're LOGGED INTO YouTube in Chrome/Edge/Firefox")
        print("2. Open your browser and verify you see your profile picture on youtube.com")
        print("3. Close and reopen your browser if needed")
        print("4. Try again")
        print("=" * 60)
        
        return 1

if __name__ == "__main__":
    sys.exit(test_youtube_download())
