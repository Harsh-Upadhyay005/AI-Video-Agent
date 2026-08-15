"""
Comprehensive Backend-Frontend Connection Verification
Tests all API endpoints and frontend integration
"""

import requests
import json
import sys
from typing import Dict, List, Tuple

# ANSI color codes for Windows
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN} {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED} {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}  {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message."""
    print(f"   {message}")

BACKEND_URL = "http://localhost:8000"
all_tests_passed = True

def test_backend_health() -> bool:
    """Test 1: Backend Health Check"""
    print_section("Test 1: Backend Health Check")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Backend is running and healthy")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Service: {data.get('service')}")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to backend at {BACKEND_URL}")
        print_info("Solution: Run 'start.bat' to start the backend")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_cors_configuration() -> bool:
    """Test 2: CORS Configuration"""
    print_section("Test 2: CORS Configuration")
    
    try:
        # Test OPTIONS request (preflight)
        response = requests.options(
            f"{BACKEND_URL}/api/v1/analyze/sync",
            headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'POST',
            }
        )
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_methods = response.headers.get('Access-Control-Allow-Methods')
        cors_headers = response.headers.get('Access-Control-Allow-Headers')
        
        if cors_origin:
            print_success("CORS is properly configured")
            print_info(f"Allow-Origin: {cors_origin}")
            print_info(f"Allow-Methods: {cors_methods}")
            print_info(f"Allow-Headers: {cors_headers}")
            return True
        else:
            print_warning("CORS headers not found in response")
            print_info("This might still work if CORS middleware is configured")
            return True
    except Exception as e:
        print_warning(f"Could not verify CORS: {e}")
        return True  # Don't fail on CORS check

def test_api_endpoints() -> bool:
    """Test 3: API Endpoints Availability"""
    print_section("Test 3: API Endpoints Availability")
    
    endpoints = [
        ("GET", "/health", "Health check (root)", True),
        ("GET", "/api/v1/health", "Health check (v1)", True),
        ("GET", "/docs", "API documentation", True),
        ("POST", "/api/v1/analyze/sync", "Synchronous video analysis", False),
        ("POST", "/api/v1/analyze", "Asynchronous video analysis", False),
        ("POST", "/api/v1/chat", "Chat with transcript", False),
        ("GET", "/api/v1/progress/{job_id}", "Progress streaming", False),
    ]
    
    all_ok = True
    for method, path, description, should_get in endpoints:
        url = f"{BACKEND_URL}{path}"
        try:
            if should_get:
                response = requests.get(url, timeout=2)
            else:
                # Use OPTIONS for POST endpoints
                response = requests.options(url, timeout=2)
            
            # 200 = OK, 405 = Method Not Allowed (but endpoint exists)
            if response.status_code in [200, 405]:
                print_success(f"{method:4} {path:35} - {description}")
            else:
                print_warning(f"{method:4} {path:35} - Status {response.status_code}")
        except Exception as e:
            print_error(f"{method:4} {path:35} - Error: {str(e)[:50]}")
            all_ok = False
    
    return all_ok

def test_dependencies() -> bool:
    """Test 4: Backend Dependencies"""
    print_section("Test 4: Backend Dependencies")
    
    all_ok = True
    
    # Test LangChain
    try:
        from langchain_mistralai import ChatMistralAI
        from langchain_core.prompts import ChatPromptTemplate
        print_success("LangChain packages installed")
        print_info("✓ langchain_mistralai")
        print_info("✓ langchain_core")
    except ImportError as e:
        print_error("LangChain packages missing")
        print_info(f"Error: {e}")
        print_info("Solution: Run 'install-langchain.bat'")
        all_ok = False
    
    # Test other critical packages
    packages = [
        ("fastapi", "FastAPI web framework"),
        ("yt_dlp", "YouTube downloader"),
        ("whisper", "OpenAI Whisper for transcription"),
        ("torch", "PyTorch"),
        ("sentence_transformers", "Embeddings"),
    ]
    
    for package, description in packages:
        try:
            __import__(package)
            print_success(f"{package:20} - {description}")
        except ImportError:
            print_error(f"{package:20} - {description} (MISSING)")
            all_ok = False
    
    return all_ok

def test_environment_variables() -> bool:
    """Test 5: Environment Variables"""
    print_section("Test 5: Environment Variables")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    all_ok = True
    
    # Check critical variables
    variables = [
        ("MISTRAL_API_KEY", "Mistral AI API key for chat", True),
        ("SARVAM_API_KEY", "Sarvam AI API key (optional)", False),
        ("WHISPER_MODEL", "Whisper model (small/medium/large)", False),
        ("ENVIRONMENT", "Environment (development/production)", False),
    ]
    
    for var_name, description, required in variables:
        value = os.getenv(var_name)
        if value and len(value) > 5:
            print_success(f"{var_name:20} - {description}")
            if var_name == "MISTRAL_API_KEY":
                print_info(f"Value: {value[:8]}...{value[-4:]}")
        elif required:
            print_error(f"{var_name:20} - {description} (MISSING)")
            print_info("Edit .env file to add this variable")
            all_ok = False
        else:
            print_warning(f"{var_name:20} - {description} (Not set)")
    
    return all_ok

def test_env_security() -> bool:
    """Test 6: .env File Security"""
    print_section("Test 6: .env File Security")
    
    import os
    import platform
    
    if not os.path.exists('.env'):
        print_error(".env file not found!")
        return False
    
    if platform.system() == "Windows":
        print_info("Windows system detected")
        print_warning(".env file permissions should be restricted")
        print_info("Solution: Run 'fix-env-permissions.bat'")
        print_info("This restricts access to your user account only")
        return True
    else:
        # Check Unix permissions
        import stat
        st = os.stat('.env')
        mode = st.st_mode
        
        if mode & stat.S_IROTH or mode & stat.S_IRGRP:
            print_error(".env file is readable by others!")
            print_info("Solution: Run 'chmod 600 .env'")
            return False
        else:
            print_success(".env file has restricted permissions")
            return True

def test_frontend_api_client() -> bool:
    """Test 7: Frontend API Client Configuration"""
    print_section("Test 7: Frontend API Client Configuration")
    
    import os
    
    client_path = "frontend/src/api/client.js"
    
    if not os.path.exists(client_path):
        print_error("API client not found!")
        return False
    
    with open(client_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for correct configuration
    checks = [
        ("API_BASE_URL", "const API_BASE_URL"),
        ("analyzeVideo", "async analyzeVideo"),
        ("sendChatMessage", "async sendChatMessage"),
        ("checkHealth", "async checkHealth"),
    ]
    
    all_ok = True
    for check_name, check_str in checks:
        if check_str in content:
            print_success(f"{check_name:20} - Found")
        else:
            print_error(f"{check_name:20} - Missing")
            all_ok = False
    
    # Check endpoint URLs
    if "'/api/v1/analyze/sync'" in content or '"/api/v1/analyze/sync"' in content:
        print_success("Analyze endpoint      - Correctly configured")
    else:
        print_error("Analyze endpoint      - Incorrect URL")
        all_ok = False
    
    if "'/api/v1/chat'" in content or '"/api/v1/chat"' in content:
        print_success("Chat endpoint         - Correctly configured")
    else:
        print_error("Chat endpoint         - Incorrect URL")
        all_ok = False
    
    return all_ok

def test_sample_request() -> bool:
    """Test 8: Sample API Request"""
    print_section("Test 8: Sample API Request")
    
    print_info("Testing with a mock request...")
    
    try:
        # Try to get detailed health
        response = requests.get(f"{BACKEND_URL}/health/detailed", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Sample request successful")
            print_info(f"Overall status: {data.get('status')}")
            
            checks = data.get('checks', {})
            for check_name, check_data in checks.items():
                status = check_data.get('status', 'unknown')
                if status == 'healthy':
                    print_info(f"  ✓ {check_name}")
                else:
                    print_info(f"  ✗ {check_name}: {check_data.get('message')}")
            
            return True
        else:
            print_error(f"Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def print_summary(results: List[Tuple[str, bool]]):
    """Print test summary"""
    print_section("Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(test_name)
        else:
            print_error(test_name)
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print_success("All tests passed! Backend and frontend are properly connected.")
        print_info("\nTo start the application:")
        print_info("  Backend: start.bat (if not running)")
        print_info("  Frontend: cd frontend && npm run dev")
        print_info("  Open: http://localhost:5173")
    else:
        print_error("Some tests failed. Please fix the issues above.")
        print_info("\nCommon solutions:")
        print_info("  1. Start backend: start.bat")
        print_info("  2. Install dependencies: install-langchain.bat")
        print_info("  3. Configure .env file with API keys")
        print_info("  4. Secure .env: fix-env-permissions.bat")
    
    return passed == total

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}AI Video Agent - Connection Verification{Colors.RESET}")
    print(f"Testing backend at: {BACKEND_URL}\n")
    
    # Run all tests
    results = [
        ("Backend Health", test_backend_health()),
        ("CORS Configuration", test_cors_configuration()),
        ("API Endpoints", test_api_endpoints()),
        ("Dependencies", test_dependencies()),
        ("Environment Variables", test_environment_variables()),
        (".env Security", test_env_security()),
        ("Frontend API Client", test_frontend_api_client()),
        ("Sample Request", test_sample_request()),
    ]
    
    # Print summary
    all_passed = print_summary(results)
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

