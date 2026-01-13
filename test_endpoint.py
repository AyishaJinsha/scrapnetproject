import requests

# Test the view_requests endpoint
url = "http://127.0.0.1:8000/view_requests/"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! The page loads correctly.")
        print(f"Content length: {len(response.text)} bytes")
    elif response.status_code == 302:
        print("⚠️ REDIRECT - You need to be logged in to access this page")
        print(f"Redirecting to: {response.headers.get('Location', 'Unknown')}")
    else:
        print(f"❌ ERROR {response.status_code}")
        print(f"Response preview:\n{response.text[:500]}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server. Make sure Django is running on port 8000")
except Exception as e:
    print(f"❌ Error: {e}")
