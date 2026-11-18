import sys
import requests

# Change this to your live public deployment URL once deployed (e.g., https://your-app.onrender.com)
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

def run_smoke_tests():
    print(f"🚀 Running smoke tests against live target: {BASE_URL}\n")

    # 1. Test Health Check Endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"- Health Check (/health): Status {response.status_code}")
        assert response.status_code == 200, f"Health check failed with status {response.status_code}"
        print("  ✅ Passed")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    # 2. Test v1 Health Check Endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        print(f"- v1 Health Check (/api/v1/health): Status {response.status_code}")
        assert response.status_code == 200, f"v1 Health check failed with status {response.status_code}"
        print("  ✅ Passed")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    # 3. Test Authentication Login (Checking response for invalid or valid credentials structure)
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
            timeout=10
        )
        print(f"- Auth Login Route (/api/v1/auth/login): Status {response.status_code}")
        # Expecting 401 Unauthorized for bad credentials, proving the endpoint is active and securing data
        assert response.status_code == 401, unexpected_status_msg(response.status_code)
        print("  ✅ Passed (Security constraint verified)")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        sys.exit(1)

    print("\n🎉 All live smoke tests passed successfully!")

def unexpected_status_msg(code):
    return f"Expected 401 for bad credentials, got {code}"

if __name__ == "__main__":
    run_smoke_tests()