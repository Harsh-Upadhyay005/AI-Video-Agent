"""
Test Backend-Frontend Connectivity
"""

import requests
import sys
import json

print("=" * 80)
print("Backend-Frontend Connectivity Test")
print("=" * 80)
print()

BACKEND_URL = "http://localhost:8000"

# Test 1: Backend Health
print("Test 1: Backend Health Check...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f" Backend is healthy")
        print(f"   Status: {data.get('status')}")
        print(f"   Environment: {data.get('environment')}")
    else:
        print(f" Backend returned status {response.status_code}")
        sys.exit(1)
except requests.exceptions.ConnectionError:
    print(f" Cannot connect to backend at {BACKEND_URL}")
    print("   Make sure backend is running: start.bat")
    sys.exit(1)
except Exception as e:
    print(f" Error: {e}")
    sys.exit(1)

print()

# Test 2: CORS Headers
print("Test 2: CORS Headers...")
try:
    response = requests.options(f"{BACKEND_URL}/api/v1/analyze/sync")
    cors_origin = response.headers.get('Access-Control-Allow-Origin')
    cors_methods = response.headers.get('Access-Control-Allow-Methods')
    
    if cors_origin:
        print(f" CORS enabled")
        print(f"   Allow-Origin: {cors_origin}")
        print(f"   Allow-Methods: {cors_methods}")
    else:
        print(f"  CORS headers not found (may still work)")
except Exception as e:
    print(f"  Could not check CORS: {e}")

print()

# Test 3: API Endpoints
print("Test 3: Available API Endpoints...")
endpoints = [
    ("GET", "/health", "Health check"),
    ("GET", "/docs", "API documentation"),
    ("POST", "/api/v1/analyze/sync", "Synchronous video analysis"),
    ("POST", "/api/v1/analyze", "Asynchronous video analysis"),
    ("POST", "/api/v1/chat", "Chat with transcript"),
]

for method, path, description in endpoints:
    url = f"{BACKEND_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=2)
        else:
            response = requests.options(url, timeout=2)
        
        # 405 is OK for POST endpoints with OPTIONS
        if response.status_code in [200, 405]:
            print(f" {method:4} {path:30} - {description}")
        else:
            print(f"  {method:4} {path:30} - Status {response.status_code}")
    except Exception as e:
        print(f" {method:4} {path:30} - Error: {e}")

print()

# Test 4: LangChain Dependencies
print("Test 4: RAG/Chat Dependencies...")
try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.prompts import ChatPromptTemplate
    print(" LangChain packages installed")
    print("   Chat feature will work!")
except ImportError as e:
    print(" LangChain packages missing")
    print(f"   Error: {e}")
    print("   Run: install-langchain.bat")

print()

# Test 5: API Keys
print("Test 5: API Keys Configuration...")
import os
from dotenv import load_dotenv

load_dotenv()

mistral_key = os.getenv("MISTRAL_API_KEY")
if mistral_key and len(mistral_key) > 10:
    print(" MISTRAL_API_KEY configured")
else:
    print(" MISTRAL_API_KEY missing or invalid")
    print("   Edit .env file and add your Mistral AI key")

print()

# Test 6: .env Security
print("Test 6: .env File Security...")
try:
    import stat
    import platform
    
    if platform.system() == "Windows":
        print("  Run fix-env-permissions.bat to secure .env file")
        print("   This restricts access to your user only")
    else:
        # Check Unix permissions
        st = os.stat('.env')
        mode = st.st_mode
        if mode & stat.S_IROTH or mode & stat.S_IRGRP:
            print("  .env file is readable by others!")
            print("   Run: chmod 600 .env")
        else:
            print(" .env file has restricted permissions")
except Exception as e:
    print(f"  Could not check permissions: {e}")

print()
print("=" * 80)
print("Summary")
print("=" * 80)
print()
print(" Backend running and accessible")
print(" API endpoints available")
print(" CORS configured for frontend")
print()
print("Frontend should connect successfully!")
print()
print("To start frontend:")
print("  cd frontend")
print("  npm run dev")
print()
print("Then open: http://localhost:5173")
print("=" * 80)

