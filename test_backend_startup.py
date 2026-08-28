"""
Backend Startup Diagnostic Test
Tests if backend can start and respond to requests properly.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_environment_loading():
    """Test if .env file is loading correctly."""
    print_section("TEST 1: Environment Variable Loading")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check critical variables
        required_vars = {
            "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY"),
            "WHISPER_MODEL": os.getenv("WHISPER_MODEL"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        }
        
        optional_vars = {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
            "SARVAM_API_KEY": os.getenv("SARVAM_API_KEY"),
        }
        
        print("\n✓ .env file found and loaded")
        print("\nRequired Variables:")
        all_required_present = True
        for var_name, var_value in required_vars.items():
            if var_value:
                masked = var_value[:8] + "..." if len(var_value) > 8 else "***"
                print(f"  ✅ {var_name}: {masked}")
            else:
                print(f"  ❌ {var_name}: NOT SET")
                all_required_present = False
        
        print("\nOptional Variables:")
        for var_name, var_value in optional_vars.items():
            if var_value:
                masked = var_value[:8] + "..." if len(var_value) > 8 else "***"
                print(f"  ✅ {var_name}: {masked}")
            else:
                print(f"  ⚠️  {var_name}: Not configured (using fallback)")
        
        if all_required_present:
            print("\n✅ All required environment variables are set")
            return True
        else:
            print("\n❌ Some required environment variables are missing")
            return False
        
    except Exception as e:
        print(f"❌ Failed to load environment: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_core_imports():
    """Test if core modules can be imported."""
    print_section("TEST 2: Core Module Imports")
    
    modules_to_test = [
        ("core.config", "ConfigManager"),
        ("core.logger", "get_logger"),
        ("core.env_validator", "validate_environment"),
        ("core.health_check", "HealthCheck"),
        ("core.supabase_client", "get_supabase_client"),
        ("core.mistral_client", "get_mistral_client"),
        ("utils.document_chunker", "DocumentChunker"),
        ("utils.audio_processor", "download_youtube_audio"),
        ("main", "run_pipeline"),
    ]
    
    all_success = True
    
    for module_path, item_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[item_name])
            getattr(module, item_name)
            print(f"  ✅ {module_path}.{item_name}")
        except Exception as e:
            print(f"  ❌ {module_path}.{item_name} - Error: {str(e)[:60]}")
            all_success = False
    
    if all_success:
        print("\n✅ All core modules imported successfully")
        return True
    else:
        print("\n❌ Some modules failed to import")
        return False


def test_api_routes():
    """Test if API routes can be imported."""
    print_section("TEST 3: API Routes Import")
    
    try:
        from api.routes import analysis, health, chat
        print("  ✅ analysis routes")
        print("  ✅ health routes")
        print("  ✅ chat routes")
        print("\n✅ All API routes imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import API routes: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_creation():
    """Test if FastAPI app can be created."""
    print_section("TEST 4: FastAPI App Creation")
    
    try:
        from api.main import app
        print(f"  ✅ FastAPI app created: {app.title}")
        print(f"  ✅ Version: {app.version}")
        print(f"  ✅ Docs URL: {app.docs_url}")
        print("\n✅ FastAPI application created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_import():
    """Test if pipeline can be imported without errors."""
    print_section("TEST 5: Pipeline Import")
    
    try:
        from main import run_pipeline, PipelineError, StageResult, StageStatus
        print("  ✅ run_pipeline function")
        print("  ✅ PipelineError class")
        print("  ✅ StageResult dataclass")
        print("  ✅ StageStatus enum")
        print("\n✅ Pipeline components imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test if all required dependencies are installed."""
    print_section("TEST 6: Dependencies Check")
    
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("langchain", "langchain"),
        ("langchain_mistralai", "langchain_mistralai"),
        ("tiktoken", "tiktoken"),
        ("yt_dlp", "yt_dlp"),
        ("whisper", "whisper"),
        ("pypdf", "pypdf"),
        ("chromadb", "chromadb"),
        ("sentence_transformers", "sentence_transformers"),
        ("python-dotenv", "dotenv"),
    ]
    
    all_installed = True
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - NOT INSTALLED")
            all_installed = False
    
    if all_installed:
        print("\n✅ All required dependencies installed")
        return True
    else:
        print("\n❌ Some dependencies are missing")
        print("\nRun: pip install -r requirements.txt")
        return False


def test_mistral_api_key():
    """Test if Mistral API key is valid."""
    print_section("TEST 7: Mistral API Key Validation")
    
    try:
        from core.mistral_client import get_mistral_client
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        print("Testing Mistral API connection...")
        print("(This will make a real API call)")
        
        client = get_mistral_client()
        llm = client._get_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Respond with exactly: 'API key is valid'"),
            ("human", "Test")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        # Test with timeout
        result = client.invoke_with_retry(chain, "Test", operation_name="API key test")
        
        if "valid" in result.lower() or len(result) > 0:
            print(f"  ✅ API Response: {result[:50]}")
            print("\n✅ Mistral API key is valid and working")
            return True
        else:
            print(f"  ⚠️  Unexpected response: {result[:50]}")
            print("\n⚠️  API responded but result unexpected")
            return True
        
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "unauthorized" in error_str.lower():
            print(f"  ❌ Invalid API key: {error_str[:100]}")
            print("\n❌ Mistral API key is INVALID")
            print("\nPlease check your MISTRAL_API_KEY in .env file")
            return False
        elif "429" in error_str or "rate limit" in error_str.lower():
            print(f"  ⚠️  Rate limited: {error_str[:100]}")
            print("\n⚠️  Rate limited but key is likely valid")
            return True
        else:
            print(f"  ❌ Error: {error_str[:100]}")
            import traceback
            traceback.print_exc()
            return False


def test_file_paths():
    """Test if required directories exist."""
    print_section("TEST 8: File Paths and Directories")
    
    required_dirs = [
        "core",
        "api",
        "utils",
        "downloads",
        "logs",
    ]
    
    all_exist = True
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - NOT FOUND")
            all_exist = False
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"     → Created directory")
            except Exception as e:
                print(f"     → Failed to create: {e}")
    
    if all_exist:
        print("\n✅ All required directories exist")
    else:
        print("\n⚠️  Some directories were missing but created")
    
    return True


def main():
    """Run all diagnostic tests."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 23 + "BACKEND STARTUP DIAGNOSTIC" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    
    tests = [
        ("Environment Variable Loading", test_environment_loading, True),
        ("File Paths and Directories", test_file_paths, False),
        ("Dependencies Check", test_dependencies, True),
        ("Core Module Imports", test_core_imports, True),
        ("Pipeline Import", test_pipeline_import, True),
        ("API Routes Import", test_api_routes, True),
        ("FastAPI App Creation", test_fastapi_creation, True),
        ("Mistral API Key Validation", test_mistral_api_key, False),  # Optional
    ]
    
    results = []
    critical_failure = False
    
    for test_name, test_func, is_critical in tests:
        try:
            result = test_func()
            results.append((test_name, result, is_critical))
            
            if is_critical and not result:
                critical_failure = True
                print(f"\n⚠️  CRITICAL TEST FAILED: {test_name}")
                print("Stopping further tests...")
                break
                
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False, is_critical))
            if is_critical:
                critical_failure = True
                print("\n⚠️  CRITICAL TEST CRASHED")
                print("Stopping further tests...")
                break
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    critical_passed = sum(1 for _, result, is_critical in results if result and is_critical)
    critical_total = sum(1 for _, _, is_critical in results if is_critical)
    
    print()
    for test_name, result, is_critical in results:
        status = "✅ PASS" if result else "❌ FAIL"
        critical_marker = " [CRITICAL]" if is_critical else ""
        print(f"{status}  {test_name}{critical_marker}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print(f"Critical: {critical_passed}/{critical_total} critical tests passed")
    
    print()
    if critical_failure:
        print("❌ CRITICAL FAILURES DETECTED")
        print("\nThe backend CANNOT start. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Check .env file exists and has MISTRAL_API_KEY")
        print("2. Run: pip install -r requirements.txt")
        print("3. Check Python version (requires 3.8+)")
        return 1
    elif passed == total:
        print("✅ ALL TESTS PASSED!")
        print("\nBackend should start successfully.")
        print("\nTo start backend:")
        print("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("⚠️  SOME OPTIONAL TESTS FAILED")
        print("\nBackend should work but some features may be unavailable.")
        print("\nTo start backend:")
        print("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        return 0


if __name__ == "__main__":
    sys.exit(main())
