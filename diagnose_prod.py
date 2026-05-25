"""Diagnose all production issues."""
import urllib.request, json, urllib.error, time

BASE = "https://grantbridge-backend-2.onrender.com/api/v1"

def req(method, path, data=None, token=None, timeout=30):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:
        return 0, {"error": str(e)}

print("=" * 60)
print("PRODUCTION DIAGNOSIS")
print("=" * 60)

# 1. Register new user
print("\n1. REGISTER new user")
ts = int(time.time())
s, b = req("POST", "/auth/register/", {
    "email": f"newuser{ts}@test.com",
    "password": "TestPass123!",
    "fullName": "New Test User",
    "role": "entrepreneur"
})
print(f"   Status: {s}")
if s == 201:
    print(f"   ✓ User created: {b.get('user', {}).get('fullName')}")
    print(f"   ✓ Token: {b.get('access', '')[:30]}...")
    new_token = b.get("access")
    new_user_id = b.get("user", {}).get("id")
else:
    print(f"   ✗ Error: {b}")
    new_token = None
    new_user_id = None

# 2. Check user appears in DB via /auth/me/
if new_token:
    print("\n2. VERIFY user saved in DB")
    s2, b2 = req("GET", "/auth/me/", token=new_token)
    print(f"   Status: {s2}")
    if s2 == 200:
        print(f"   ✓ User in DB: {b2.get('fullName')} | verified={b2.get('verificationStatus')}")
    else:
        print(f"   ✗ Error: {b2}")

# 3. Profile update with PATCH
if new_token:
    print("\n3. PROFILE UPDATE (PATCH /auth/me/)")
    s3, b3 = req("PATCH", "/auth/me/", {
        "fullName": "Updated Name",
        "phone": "+2348012345678",
        "company": "Test Company",
        "location": "Lagos, Nigeria",
        "bio": "Test bio"
    }, token=new_token)
    print(f"   Status: {s3}")
    if s3 == 200:
        print(f"   ✓ Name updated: {b3.get('fullName')}")
        print(f"   ✓ Phone: {b3.get('phone')}")
        print(f"   ✓ Company: {b3.get('company')}")
    else:
        print(f"   ✗ Error: {b3}")

# 4. Create pitch
if new_token:
    print("\n4. CREATE PITCH")
    s4, b4 = req("POST", "/pitches/", {
        "title": "Test Pitch from Diagnosis",
        "description": "A test pitch to verify production DB is saving correctly.",
        "category": "FinTech",
        "amountNeeded": "2000000.00",
        "stage": "idea",
        "location": "Lagos, Nigeria",
        "tags": ["test", "fintech"]
    }, token=new_token)
    print(f"   Status: {s4}")
    if s4 == 201:
        print(f"   ✓ Pitch created: {b4.get('title')}")
        print(f"   ✓ ID: {b4.get('id')}")
    else:
        print(f"   ✗ Error: {b4}")

# 5. Check pitches list
print("\n5. PITCHES LIST")
s5, b5 = req("GET", "/pitches/")
print(f"   Status: {s5}")
print(f"   Count: {b5.get('count', 0)}")

# 6. Login with demo account
print("\n6. LOGIN demo account")
s6, b6 = req("POST", "/auth/login/", {
    "email": "entrepreneur@demo.com",
    "password": "demo1234",
    "role": "entrepreneur"
})
print(f"   Status: {s6}")
if s6 == 200:
    print(f"   ✓ Login OK: {b6.get('user', {}).get('fullName')}")
else:
    print(f"   ✗ Error: {b6}")

# 7. Check media upload endpoint
if new_token:
    print("\n7. MEDIA UPLOAD endpoint exists")
    s7, b7 = req("GET", "/pitches/upload-media/", token=new_token)
    print(f"   Status: {s7} (405=exists, 404=missing)")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
