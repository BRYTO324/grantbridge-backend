"""Test email sending on production."""
import urllib.request, json

BASE = "https://grantbridge-backend-2.onrender.com/api/v1"

# Register a new user — this triggers email sending
import time
ts = int(time.time())
email = f"emailtest{ts}@gmail.com"

req = urllib.request.Request(
    f"{BASE}/auth/register/",
    data=json.dumps({
        "email": email,
        "password": "TestPass123!",
        "fullName": "Email Test User",
        "role": "entrepreneur"
    }).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
        print(f"✓ Register OK in {r.status}")
        print(f"  User: {data.get('user', {}).get('fullName')}")
        print(f"  Token: {data.get('access', '')[:20]}...")
        print(f"\nCheck {email} inbox for verification email.")
        print("If no email received, check Render logs for SMTP errors.")
except Exception as e:
    print(f"✗ Failed: {e}")
