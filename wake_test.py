"""Test the live production API endpoints."""
import urllib.request, json, urllib.error

BASE = "https://grantbridge-backend-2.onrender.com/api/v1"

print("Testing production API...")

# Test 1: Health check
try:
    with urllib.request.urlopen("https://grantbridge-backend-2.onrender.com/", timeout=60) as r:
        data = json.loads(r.read())
        print(f"✓ Health: {data}")
except Exception as e:
    print(f"✗ Health failed: {e}")

# Test 2: Register
try:
    req = urllib.request.Request(
        f"{BASE}/auth/register/",
        data=json.dumps({
            "email": "prodtest@grantbridge.com",
            "password": "TestPass123!",
            "fullName": "Prod Test",
            "role": "entrepreneur"
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
        print(f"✓ Register: user={data.get('user', {}).get('fullName')}, token={data.get('access', '')[:20]}...")
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    print(f"✗ Register HTTP {e.code}: {err}")
except Exception as e:
    print(f"✗ Register failed: {e}")

# Test 3: Login
try:
    req2 = urllib.request.Request(
        f"{BASE}/auth/login/",
        data=json.dumps({
            "email": "entrepreneur@demo.com",
            "password": "demo1234",
            "role": "entrepreneur"
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req2, timeout=60) as r:
        data = json.loads(r.read())
        print(f"✓ Login: user={data.get('user', {}).get('fullName')}, token={data.get('access', '')[:20]}...")
except urllib.error.HTTPError as e:
    err = json.loads(e.read())
    print(f"✗ Login HTTP {e.code}: {err}")
except Exception as e:
    print(f"✗ Login failed: {e}")

# Test 4: Pitches
try:
    with urllib.request.urlopen(f"{BASE}/pitches/", timeout=60) as r:
        data = json.loads(r.read())
        print(f"✓ Pitches: count={data.get('count')}")
except Exception as e:
    print(f"✗ Pitches failed: {e}")

print("\nDone.")
