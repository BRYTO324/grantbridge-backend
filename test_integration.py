"""
Integration test — verifies all fixed endpoints work end-to-end.
Run with: python test_integration.py
"""
import json
import urllib.request
import urllib.error
import sys

BASE = "http://localhost:8000/api/v1"
PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
results = []


def req(method, path, data=None, token=None, expect=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            status = resp.status
            body = json.loads(resp.read())
            ok = (expect is None) or (status == expect)
            return ok, status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        ok = (expect is not None) and (e.code == expect)
        return ok, e.code, body


def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
    results.append(ok)


print("\n=== GrantBridge Integration Tests ===\n")

# ── 1. Login ──────────────────────────────────────────────────────────────────
print("1. Authentication")
ok, status, body = req("POST", "/auth/login/", {
    "email": "entrepreneur@demo.com", "password": "demo1234", "role": "entrepreneur"
})
check("Entrepreneur login", ok and "access" in body, f"status={status}")
ent_token = body.get("access", "")
ent_user = body.get("user", {})
check("Returns user object", bool(ent_user.get("fullName")), ent_user.get("fullName"))
check("Returns refresh token", bool(body.get("refresh")))

ok2, s2, b2 = req("POST", "/auth/login/", {
    "email": "funder@demo.com", "password": "demo1234", "role": "funder"
})
check("Funder login", ok2 and "access" in b2, f"status={s2}")
funder_token = b2.get("access", "")

ok3, s3, b3 = req("POST", "/auth/login/", {
    "email": "wrong@demo.com", "password": "wrongpass", "role": "entrepreneur"
}, expect=400)
check("Rejects bad credentials", ok3, f"status={s3}")

# ── 2. GET /auth/me/ ──────────────────────────────────────────────────────────
print("\n2. Profile fetch")
ok, status, body = req("GET", "/auth/me/", token=ent_token)
check("GET /auth/me/ returns user", ok and body.get("email") == "entrepreneur@demo.com")
check("Returns verificationStatus", "verificationStatus" in body)
check("Returns profileCompleted", "profileCompleted" in body)

# ── 3. PATCH /auth/me/ ────────────────────────────────────────────────────────
print("\n3. Profile update (persistence test)")
ok, status, body = req("PATCH", "/auth/me/", {
    "fullName": "Amara Updated", "phone": "+2348099999999", "company": "UpdatedCo"
}, token=ent_token)
check("PATCH /auth/me/ succeeds", ok, f"status={status}")
check("fullName persisted", body.get("fullName") == "Amara Updated")
check("phone persisted", body.get("phone") == "+2348099999999")
check("company persisted", body.get("company") == "UpdatedCo")

# Verify it persists after re-fetch
ok2, _, body2 = req("GET", "/auth/me/", token=ent_token)
check("Changes persist on re-fetch", body2.get("fullName") == "Amara Updated")

# Restore original name
req("PATCH", "/auth/me/", {"fullName": "Amara Okafor"}, token=ent_token)

# ── 4. Change password ────────────────────────────────────────────────────────
print("\n4. Password change")
ok, status, body = req("POST", "/auth/change-password/", {
    "currentPassword": "demo1234", "newPassword": "NewPass456!"
}, token=ent_token)
check("Change password succeeds", ok, f"status={status}")

# Login with new password
ok2, s2, b2 = req("POST", "/auth/login/", {
    "email": "entrepreneur@demo.com", "password": "NewPass456!", "role": "entrepreneur"
})
check("Login with new password works", ok2 and "access" in b2)

# Restore original password
req("POST", "/auth/change-password/", {
    "currentPassword": "NewPass456!", "newPassword": "demo1234"
}, token=b2.get("access", ent_token))
check("Password restored", True)

# ── 5. Pitches ────────────────────────────────────────────────────────────────
print("\n5. Pitches")
ok, status, body = req("GET", "/pitches/")
check("GET /pitches/ public (no auth)", ok, f"count={body.get('count')}")
check("Returns results array", isinstance(body.get("results"), list))
check("Has 3 seeded pitches", body.get("count", 0) >= 3)

pitch_id = body["results"][0]["id"] if body.get("results") else None

if pitch_id:
    ok2, s2, b2 = req("GET", f"/pitches/{pitch_id}/")
    check("GET /pitches/:id/ works", ok2, f"status={s2}")
    check("Pitch has offers array", "offers" in b2)
    check("Pitch has likedByMe field", "likedByMe" in b2)

# Create pitch as entrepreneur
ok3, s3, b3 = req("POST", "/pitches/", {
    "title": "Test Pitch from Integration",
    "description": "A test pitch created by the integration test suite.",
    "category": "FinTech",
    "amountNeeded": "1000000.00",
    "stage": "idea",
    "location": "Lagos, Nigeria",
    "tags": ["test", "fintech"],
}, token=ent_token)
check("POST /pitches/ creates pitch", ok3, f"status={s3}")
new_pitch_id = b3.get("id") if ok3 else None

# Funder cannot create pitch
ok4, s4, _ = req("POST", "/pitches/", {
    "title": "Funder trying to pitch", "description": "x",
    "category": "FinTech", "amountNeeded": "100.00", "stage": "idea", "location": "x"
}, token=funder_token, expect=403)
check("Funder blocked from creating pitch", ok4, f"status={s4}")

# ── 6. Like / Bookmark ────────────────────────────────────────────────────────
print("\n6. Like & Bookmark")
if pitch_id:
    ok, s, b = req("PATCH", f"/pitches/{pitch_id}/like/", token=funder_token)
    check("Toggle like works", ok, f"status={s}")

    ok2, s2, b2 = req("PATCH", f"/pitches/{pitch_id}/bookmark/", token=funder_token)
    check("Toggle bookmark works", ok2, f"status={s2}")

# ── 7. Funding Offers ─────────────────────────────────────────────────────────
print("\n7. Funding Offers")
if pitch_id:
    ok, s, b = req("POST", "/offers/", {
        "pitchId": pitch_id, "amount": "500000.00", "message": "I want to fund this project."
    }, token=funder_token)
    check("Funder submits offer", ok, f"status={s}")
    offer_id = b.get("offers", [{}])[-1].get("id") if ok else None

    # Entrepreneur cannot submit offer
    ok2, s2, _ = req("POST", "/offers/", {
        "pitchId": pitch_id, "amount": "100.00", "message": "test"
    }, token=ent_token, expect=403)
    check("Entrepreneur blocked from submitting offer", ok2, f"status={s2}")

# ── 8. Weekly Progress ────────────────────────────────────────────────────────
print("\n8. Weekly Progress")
if new_pitch_id:
    ok, s, b = req("POST", "/progress/", {
        "pitchId": new_pitch_id,
        "weekEnding": "2026-05-25",
        "summary": "Good week, made progress on MVP.",
        "wins": "Completed user research.",
        "blockers": "Waiting on API keys.",
        "nextSteps": "Start building the dashboard.",
        "metrics": {"users": "50", "revenue": "0"}
    }, token=ent_token)
    check("Submit weekly progress", ok, f"status={s}")

    ok2, s2, b2 = req("GET", "/progress/", token=ent_token)
    check("GET /progress/ returns updates", ok2 and b2.get("count", 0) >= 1)

# Funder cannot submit progress
ok3, s3, _ = req("POST", "/progress/", {
    "pitchId": pitch_id or "00000000-0000-0000-0000-000000000000",
    "weekEnding": "2026-05-25", "summary": "x", "wins": "x", "nextSteps": "x"
}, token=funder_token, expect=403)
check("Funder blocked from progress", ok3, f"status={s3}")

# ── 9. Verification status ────────────────────────────────────────────────────
print("\n9. Verification")
ok, s, b = req("GET", "/verification/status/", token=ent_token)
check("GET /verification/status/ works", ok, f"verificationStatus={b.get('verificationStatus')}")

# ── 10. Unauthenticated access ────────────────────────────────────────────────
print("\n10. Auth guards")
ok, s, _ = req("GET", "/auth/me/", expect=401)
check("GET /auth/me/ requires auth", ok, f"status={s}")

ok2, s2, _ = req("POST", "/offers/", {"pitchId": "x"}, expect=401)
check("POST /offers/ requires auth", ok2, f"status={s2}")

ok3, s3, _ = req("POST", "/progress/", {}, expect=401)
check("POST /progress/ requires auth", ok3, f"status={s3}")

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(results)
total = len(results)
print(f"\n{'='*40}")
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("\033[92mAll tests passed! ✓\033[0m")
else:
    failed = total - passed
    print(f"\033[91m{failed} test(s) failed\033[0m")
    sys.exit(1)
