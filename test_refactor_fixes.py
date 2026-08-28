"""
Quick test to verify refactoring fixes.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_stt_service_init():
    """Test STT service initialization."""
    print("\n[Test 1] STT Service Initialization")
    try:
        from core.stt_service import get_stt_service
        
        stt_service = get_stt_service()
        print("✓ STT service initialized successfully")
        return True
    except Exception as e:
        print(f"✗ STT service failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audio_pipeline_init():
    """Test Audio pipeline initialization."""
    print("\n[Test 2] Audio Pipeline Initialization")
    try:
        from core.audio_pipeline import AudioPipeline
        
        pipeline = AudioPipeline()
        print("✓ Audio pipeline initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Audio pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_source_type_detection():
    """Test source type detection."""
    print("\n[Test 3] Source Type Detection")
    try:
        from core.source_types import SourceType
        
        # Test YouTube
        yt_type = SourceType.from_source("https://www.youtube.com/watch?v=test")
        assert yt_type == SourceType.YOUTUBE, f"Expected YOUTUBE, got {yt_type}"
        print("✓ YouTube detection works")
        
        # Test PDF
        pdf_type = SourceType.from_source("document.pdf")
        assert pdf_type == SourceType.PDF, f"Expected PDF, got {pdf_type}"
        print("✓ PDF detection works")
        
        # Test Audio
        audio_type = SourceType.from_source("audio.mp3")
        assert audio_type == SourceType.AUDIO, f"Expected AUDIO, got {audio_type}"
        print("✓ Audio detection works")
        
        return True
    except Exception as e:
        print(f"✗ Source type detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_supabase_status():
    """Test Supabase configuration status."""
    print("\n[Test 4] Supabase Configuration Status")
    try:
        from core.supabase_client import get_supabase_status
        
        status = get_supabase_status()
        print(f"  SDK Installed: {status['sdk_installed']}")
        print(f"  URL Configured: {status['url_configured']}")
        print(f"  Key Configured: {status['key_configured']}")
        print(f"  Available: {status['available']}")
        
        if status['error']:
            print(f"  Error: {status['error']}")
        
        if not status['available']:
            print("ℹ  Supabase not available (this is OK, will use local fallback)")
        else:
            print("✓ Supabase is available")
        
        return True
    except Exception as e:
        print(f"✗ Supabase status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager():
    """Test Config Manager."""
    print("\n[Test 5] Config Manager")
    try:
        from core.config import ConfigManager
        
        # Initialize if not already
        config = ConfigManager.initialize()
        print(f"✓ Config initialized: {config.environment} environment")
        
        # Test get_config
        config2 = ConfigManager.get_config()
        assert config is config2, "Config should be singleton"
        print("✓ Config singleton works")
        
        return True
    except Exception as e:
        print(f"✗ Config manager failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("REFACTORING FIXES - VERIFICATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Config Manager", test_config_manager),
        ("STT Service Init", test_stt_service_init),
        ("Audio Pipeline Init", test_audio_pipeline_init),
        ("Source Type Detection", test_source_type_detection),
        ("Supabase Status", test_supabase_status),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}  {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Refactoring fixes verified!")
        return 0
    else:
        print(f"\n⚠  {total - passed} test(s) failed - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
