"""Test the analyze endpoint with a short video"""
import requests
import json
import time

API_URL = "http://localhost:8000"

print("=" * 60)
print("TESTING ANALYZE ENDPOINT")
print("=" * 60)

# Test 1: Health check
print("\n[1/3] Testing health endpoint...")
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    print(f"✅ Health check: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Health check failed: {e}")
    exit(1)

# Test 2: Async analyze (should return immediately with job_id)
print("\n[2/3] Testing async analyze endpoint...")
try:
    payload = {
        "source": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # 18 second video
        "language": "english"
    }
    
    print(f"Sending request to: {API_URL}/api/v1/analyze")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{API_URL}/api/v1/analyze",
        json=payload,
        timeout=10
    )
    
    print(f"✅ Status code: {response.status_code}")
    result = response.json()
    print(f"✅ Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200 and "job_id" in result:
        job_id = result["job_id"]
        print(f"\n✅ Got job_id: {job_id}")
        print(f"   You can monitor progress at: {API_URL}/api/v1/progress/{job_id}")
        
        # Test 3: Check progress endpoint
        print(f"\n[3/3] Testing progress endpoint...")
        print("Checking progress for 5 seconds...")
        
        for i in range(5):
            time.sleep(1)
            try:
                # Note: This will be an SSE stream, so we can't easily parse it
                # Just check if endpoint is accessible
                response = requests.get(
                    f"{API_URL}/api/v1/progress/{job_id}",
                    timeout=2,
                    stream=True
                )
                print(f"   Progress endpoint accessible: {response.status_code}")
                break
            except Exception as e:
                print(f"   Waiting... ({i+1}/5)")
    else:
        print(f"❌ Unexpected response: {result}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out - backend may be hanging")
except Exception as e:
    print(f"❌ Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
