"""
Backend verification script.
Run this to ensure the backend is ready for frontend development.
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_check(passed, message):
    """Print a check result."""
    icon = "[okay]" if passed else "[wrong]"
    print(f"{icon} {message}")
    return passed

def verify_file_structure():
    """Verify all required files exist."""
    print_header("1. File Structure Verification")
    
    required_files = [
        "api/main.py",
        "api/routes/health.py",
        "api/routes/analysis.py",
        "api/routes/chat.py",
        "core/logger.py",
        "core/config.py",
        "core/validators.py",
        "core/exceptions.py",
        "core/security.py",
        "core/health_check.py",
        "core/api_utils.py",
        "core/resource_manager.py",
        "core/env_validator.py",
        "core/transcriber.py",
        "core/summarizer.py",
        "core/extractor.py",
        "core/rag_engine.py",
        "core/vector_store.py",
        "utils/audio_processor.py",
        "requirements.txt",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
    ]
    
    all_exist = True
    for file in required_files:
        exists = Path(file).exists()
        if not print_check(exists, f"{file}"):
            all_exist = False
    
    return all_exist

def verify_environment():
    """Verify environment variables."""
    print_header("2. Environment Configuration")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    print_check(env_example.exists(), ".env.example file exists")
    
    if env_file.exists():
        print_check(True, ".env file exists")
        
        # Check for required variables
        with open(".env", "r") as f:
            env_content = f.read()
        
        has_mistral = "MISTRAL_API_KEY" in env_content and "your_mistral" not in env_content
        print_check(has_mistral, "MISTRAL_API_KEY is configured")
        
        has_sarvam = "SARVAM_API_KEY" in env_content
        if has_sarvam:
            print_check(True, "SARVAM_API_KEY is configured (optional)")
        else:
            print_check(True, "SARVAM_API_KEY not configured (optional - needed for Hinglish)")
        
        return has_mistral
    else:
        print_check(False, ".env file exists - PLEASE CREATE FROM .env.example")
        print("   Run: copy .env.example .env")
        return False

def verify_dependencies():
    """Verify Python dependencies."""
    print_header("3. Python Dependencies")
    
    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("whisper", "OpenAI Whisper"),
        ("langchain", "LangChain"),
        ("chromadb", "ChromaDB"),
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print_check(True, f"{name} installed")
        except ImportError:
            print_check(False, f"{name} NOT installed")
            all_installed = False
    
    if not all_installed:
        print("\n⚠️  Install missing dependencies:")
        print("   pip install -r requirements.txt")
    
    return all_installed

def verify_directories():
    """Verify required directories."""
    print_header("4. Directory Structure")
    
    required_dirs = [
        "api",
        "api/routes",
        "core",
        "utils",
        "tests",
    ]
    
    all_exist = True
    for directory in required_dirs:
        exists = Path(directory).is_dir()
        if not print_check(exists, f"{directory}/ directory"):
            all_exist = False
    
    # Check if data directories will be created
    data_dirs = ["downloads", "logs", "vector_db"]
    print("\nData directories (created on first run):")
    for directory in data_dirs:
        exists = Path(directory).exists()
        status = "exists" if exists else "will be created"
        print(f"   {directory}/ - {status}")
    
    return all_exist

def verify_api_structure():
    """Verify API structure."""
    print_header("5. API Structure")
    
    checks = []
    
    # Check if main.py has required components
    main_file = Path("api/main.py")
    if main_file.exists():
        with open(main_file, "r") as f:
            content = f.read()
        
        checks.append(print_check("FastAPI" in content, "FastAPI app created"))
        checks.append(print_check("CORSMiddleware" in content, "CORS middleware configured"))
        checks.append(print_check("lifespan" in content, "Lifespan management"))
        checks.append(print_check("include_router" in content, "Routes included"))
    else:
        checks.append(print_check(False, "api/main.py exists"))
    
    return all(checks)

def verify_documentation():
    """Verify documentation."""
    print_header("6. Documentation")
    
    docs = [
        ("README.md", "Main README"),
        ("PRODUCTION_READY_CHANGES.md", "Production changes documentation"),
        ("DEPLOYMENT_QUICKSTART.md", "Deployment guide"),
        ("FRONTEND_INTEGRATION_GUIDE.md", "Frontend integration guide"),
        ("tests/README.md", "Testing documentation"),
    ]
    
    all_exist = True
    for file, name in docs:
        exists = Path(file).exists()
        if not print_check(exists, f"{name}"):
            all_exist = False
    
    return all_exist

def print_next_steps():
    """Print next steps."""
    print_header("Next Steps")
    
    print("""
1. Configure Environment:
   copy .env.example .env
   # Edit .env and add your MISTRAL_API_KEY

2. Install Dependencies (if not done):
   pip install -r requirements.txt

3. Start Backend:
   # Development (with hot reload)
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   
   # OR with Docker
   docker-compose up --build

4. Verify Backend is Running:
   # Open in browser
   http://localhost:8000/docs
   
   # Or check health
   curl http://localhost:8000/health

5. Start Frontend Development:
   # Read FRONTEND_INTEGRATION_GUIDE.md for React integration examples
   # All API endpoints are documented at /docs

6. Test API Endpoints:
   # Use the interactive docs at /docs to test all endpoints
""")

def main():
    """Run all verifications."""
    print("\n" + "=" * 80)
    print("  AI Video Agent Backend Verification")
    print("=" * 80)
    
    results = []
    
    results.append(("File Structure", verify_file_structure()))
    results.append(("Environment", verify_environment()))
    results.append(("Dependencies", verify_dependencies()))
    results.append(("Directories", verify_directories()))
    results.append(("API Structure", verify_api_structure()))
    results.append(("Documentation", verify_documentation()))
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        icon = "[okay]" if result else "[wrong]"
        print(f"{icon} {name}: {'PASS' if result else 'FAIL'}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n Backend is 100% READY for frontend development!")
        print("   Read FRONTEND_INTEGRATION_GUIDE.md to get started with React.")
    else:
        print("\n  Some checks failed. Please fix the issues above.")
        print("   Most issues can be fixed by:")
        print("   1. Creating .env file from .env.example")
        print("   2. Installing dependencies: pip install -r requirements.txt")
    
    print_next_steps()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
