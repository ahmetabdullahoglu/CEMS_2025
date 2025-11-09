"""
Test Login Endpoint
Direct API test for authentication
"""

import asyncio
import sys
import httpx
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_login():
    """Test login endpoint directly"""
    print("=" * 70)
    print("🔐 Testing Login Endpoint")
    print("=" * 70)
    print()

    # Test credentials
    credentials = {
        "username": "admin",
        "password": "Admin@123"
    }

    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/auth/login"

    print("📍 Testing endpoint:", login_url)
    print("📝 Credentials:", credentials)
    print()

    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Health check
            print("1️⃣  Checking if API is running...")
            try:
                response = await client.get(f"{base_url}/docs")
                if response.status_code == 200:
                    print("✅ API is running")
                else:
                    print(f"⚠️  Unexpected response: {response.status_code}")
            except Exception as e:
                print(f"❌ API is not accessible: {e}")
                print()
                print("💡 Make sure Docker containers are running:")
                print("   docker compose up -d")
                print("   docker compose logs app")
                return
            print()

            # Test 2: Login attempt
            print("2️⃣  Attempting login...")
            try:
                response = await client.post(
                    login_url,
                    json=credentials,
                    headers={"Content-Type": "application/json"}
                )

                print(f"   Status Code: {response.status_code}")
                print(f"   Response Headers: {dict(response.headers)}")
                print()

                if response.status_code == 200:
                    print("✅ LOGIN SUCCESSFUL!")
                    print()
                    data = response.json()
                    print("📦 Response Data:")
                    print(f"   Access Token: {data.get('access_token', 'N/A')[:50]}...")
                    print(f"   Refresh Token: {data.get('refresh_token', 'N/A')[:50]}...")
                    print(f"   Token Type: {data.get('token_type', 'N/A')}")

                    if 'user' in data:
                        user = data['user']
                        print(f"\n👤 User Info:")
                        print(f"   Username: {user.get('username')}")
                        print(f"   Email: {user.get('email')}")
                        print(f"   Full Name: {user.get('full_name')}")
                        print(f"   Is Active: {user.get('is_active')}")
                        print(f"   Is Superuser: {user.get('is_superuser')}")

                elif response.status_code == 401:
                    print("❌ LOGIN FAILED - 401 Unauthorized")
                    print()
                    try:
                        error_data = response.json()
                        print("📦 Error Response:")
                        print(f"   {error_data}")
                    except:
                        print("📦 Raw Response:")
                        print(f"   {response.text}")
                    print()
                    print("🔍 Possible Issues:")
                    print("   1. Password is incorrect")
                    print("   2. User doesn't exist in database")
                    print("   3. User account is disabled or locked")
                    print("   4. Password hashing mismatch")
                    print()
                    print("💡 Run diagnostics:")
                    print("   python scripts/debug_auth.py")

                elif response.status_code == 422:
                    print("❌ VALIDATION ERROR - 422 Unprocessable Entity")
                    print()
                    error_data = response.json()
                    print("📦 Validation Errors:")
                    for error in error_data.get('detail', []):
                        print(f"   - {error.get('loc')}: {error.get('msg')}")
                    print()
                    print("💡 Check that:")
                    print("   - Username is at least 3 characters")
                    print("   - Password is at least 8 characters")

                else:
                    print(f"❌ UNEXPECTED ERROR - {response.status_code}")
                    print()
                    print("📦 Response:")
                    print(f"   {response.text}")

            except httpx.RequestError as e:
                print(f"❌ Request failed: {e}")
                print()
                print("💡 Make sure the application is running:")
                print("   docker compose up -d")

            print()

            # Test 3: Try with wrong password
            print("3️⃣  Testing with wrong password...")
            wrong_credentials = {
                "username": "admin",
                "password": "WrongPassword123"
            }

            response = await client.post(
                login_url,
                json=wrong_credentials,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 401:
                print("✅ Correctly rejected wrong password (401)")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")

            print()
            print("=" * 70)
            print("🏁 Test Complete")
            print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_login())
