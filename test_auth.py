import requests
import sys

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    email = "testuser@example.com"
    password = "password123"

    print(f"1. Registering user: {email}")
    response = requests.post(f"{BASE_URL}/register", json={"email": email, "password": password})
    if response.status_code == 200:
        print("   Registration successful!")
    elif response.status_code == 400 and "already registered" in response.text:
        print("   User already registered, proceeding to login.")
    else:
        print(f"   Registration failed: {response.text}")
        sys.exit(1)

    print("\n2. Logging in")
    response = requests.post(f"{BASE_URL}/token", data={"username": email, "password": password})
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print("   Login successful! Token received.")
    else:
        print(f"   Login failed: {response.text}")
        sys.exit(1)

    print("\n3. Accessing protected route (/transcripts)")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/transcripts", headers=headers)
    if response.status_code == 200:
        print(f"   Access successful! Transcripts: {response.json()}")
    else:
        print(f"   Access failed: {response.text}")
        sys.exit(1)

    print("\n4. Accessing protected route WITHOUT token")
    response = requests.get(f"{BASE_URL}/transcripts")
    if response.status_code == 401:
        print("   Access denied as expected.")
    else:
        print(f"   Unexpected status code: {response.status_code}")
        sys.exit(1)

    print("\n✅ Auth flow verified successfully!")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
