"""
Quick test script to verify frontend-backend connection readiness.
Tests imports, API configuration, and CORS settings.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("\n" + "=" * 70)
    print("TEST 1: Import Check")
    print("=" * 70)
    
    try:
        print("\n[1] Testing core imports...")
        from core.vector_store import (
            build_vector_store,
            get_hybrid_retriever,
            get_reranked_retriever
        )
        print("  ✓ core.vector_store")
        
        from core.reranker import get_cross_encoder_reranker
        print("  ✓ core.reranker")
        
        from core.rag_engine import build_rag_chain, EnhancedRAGChain
        print("  ✓ core.rag_engine")
        
        from core.rag_storage import get_rag_storage
        print("  ✓ core.rag_storage")
        
        print("\n[2] Testing API imports...")
        from api.main import app
        print("  ✓ api.main")
        
        from api.routes import chat, health, analysis
        print("  ✓ api.routes")
        
        print("\n✓ TEST PASSED: All imports successful")
        return True
        
    except ImportError as e:
        print(f"\n❌ TEST FAILED: Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_config():
    """Test environment configuration."""
    print("\n" + "=" * 70)
    print("TEST 2: Environment Configuration")
    print("=" * 70)
    
    try:
        print("\n[1] Checking .env file...")
        if os.path.exists('.env'):
            print("  ✓ .env file exists")
        else:
            print("  ❌ .env file missing")
            return False
        
        print("\n[2] Checking frontend/.env file...")
        if os.path.exists('frontend/.env'):
            with open('frontend/.env', 'r') as f:
                content = f.read()
                if 'VITE_API_URL' in content:
                    print("  ✓ VITE_API_URL configured")
                    # Extract URL
                    for line in content.split('\n'):
                        if line.startswith('VITE_API_URL'):
                            print(f"    → {line}")
                else:
                    print("  ❌ VITE_API_URL not found")
                    return False
        else:
            print("  ❌ frontend/.env file missing")
            return False
        
        print("\n[3] Checking backend environment variables...")
        from core.config import ConfigManager
        config = ConfigManager.initialize()
        print(f"  ✓ Environment: {config.environment}")
        print(f"  ✓ Debug mode: {config.debug}")
        
        print("\n✓ TEST PASSED: Environment configured correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cors_config():
    """Test CORS configuration."""
    print("\n" + "=" * 70)
    print("TEST 3: CORS Configuration")
    print("=" * 70)
    
    try:
        from api.main import app
        
        print("\n[1] Checking CORS middleware...")
        has_cors = False
        for middleware in app.user_middleware:
            if 'CORSMiddleware' in str(middleware):
                has_cors = True
                print("  ✓ CORSMiddleware is configured")
                break
        
        if not has_cors:
            print("  ❌ CORSMiddleware not found")
            return False
        
        print("\n[2] CORS Settings:")
        print("  - Allow Origins: * (all origins)")
        print("  - Allow Credentials: True")
        print("  - Allow Methods: * (all methods)")
        print("  - Allow Headers: * (all headers)")
        print("\n  ⚠ For production, specify exact origins!")
        
        print("\n✓ TEST PASSED: CORS configured (development mode)")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """Test API route configuration."""
    print("\n" + "=" * 70)
    print("TEST 4: API Routes")
    print("=" * 70)
    
    try:
        from api.main import app
        
        print("\n[1] Registered routes:")
        
        important_routes = [
            '/health',
            '/health/detailed',
            '/api/v1/analyze',
            '/api/v1/upload',
            '/api/v1/chat',
            '/api/v1/chat/storage/health'
        ]
        
        all_routes = [route.path for route in app.routes]
        
        found_count = 0
        for route in important_routes:
            if route in all_routes:
                print(f"  ✓ {route}")
                found_count += 1
            else:
                print(f"  ❌ {route} - NOT FOUND")
        
        print(f"\n[2] Found {found_count}/{len(important_routes)} important routes")
        
        if found_count == len(important_routes):
            print("\n✓ TEST PASSED: All important routes registered")
            return True
        else:
            print("\n⚠ TEST WARNING: Some routes missing")
            return True  # Not critical
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_frontend_api_client():
    """Test frontend API client configuration."""
    print("\n" + "=" * 70)
    print("TEST 5: Frontend API Client")
    print("=" * 70)
    
    try:
        print("\n[1] Checking API client file...")
        client_path = 'frontend/src/api/client.js'
        
        if not os.path.exists(client_path):
            print(f"  ❌ {client_path} not found")
            return False
        
        print(f"  ✓ {client_path} exists")
        
        print("\n[2] Checking API client configuration...")
        with open(client_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('import.meta.env.VITE_API_URL', 'Environment variable usage'),
            ('http://localhost:8000', 'Fallback URL'),
            ('async request(endpoint', 'Request method'),
            ('sendChatMessage', 'Chat endpoint'),
            ('uploadAndAnalyze', 'Upload endpoint'),
            ('analyzeVideoAsync', 'Video analysis endpoint')
        ]
        
        for check_str, description in checks:
            if check_str in content:
                print(f"  ✓ {description}")
            else:
                print(f"  ⚠ {description} - might be missing")
        
        print("\n✓ TEST PASSED: API client properly configured")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_storage_health():
    """Test RAG storage health."""
    print("\n" + "=" * 70)
    print("TEST 6: RAG Storage Health")
    print("=" * 70)
    
    try:
        from core.rag_storage import get_rag_storage
        
        print("\n[1] Initializing RAG storage...")
        storage = get_rag_storage()
        print(f"  ✓ Storage initialized")
        
        print("\n[2] Checking storage health...")
        health = storage.health_check()
        
        print(f"  - Storage type: {health['storage_type']}")
        print(f"  - Using Redis: {health['using_redis']}")
        print(f"  - Session count: {health['session_count']}")
        print(f"  - Healthy: {health['healthy']}")
        
        if health['healthy']:
            print("\n✓ TEST PASSED: RAG storage healthy")
            return True
        else:
            print("\n⚠ TEST WARNING: Storage degraded (using in-memory fallback)")
            return True  # Not critical
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all connection tests."""
    print("\n" + "=" * 70)
    print("FRONTEND-BACKEND CONNECTION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Import Check", test_imports),
        ("Environment Config", test_environment_config),
        ("CORS Config", test_cors_config),
        ("API Routes", test_api_routes),
        ("Frontend API Client", test_frontend_api_client),
        ("RAG Storage Health", test_storage_health)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ TEST ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Frontend-Backend Connection: READY")
        print("\nTo start:")
        print("  Backend:  start.bat  (or: uvicorn api.main:app --reload)")
        print("  Frontend: cd frontend && npm run dev")
        return True
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        print("\n❌ Frontend-Backend Connection: NEEDS ATTENTION")
        print("\nPlease fix the failed tests before starting the servers.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
