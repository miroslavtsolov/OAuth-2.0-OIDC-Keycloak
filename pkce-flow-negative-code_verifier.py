#!/usr/bin/env python3
"""
NEGATIVE TEST: PKCE flow that is expected to FAIL.

Same flow as pkce-flow.py, but the code_verifier is deliberately corrupted
and not sent in the token request, so Keycloak should reject the exchange
(invalid_grant / PKCE verification failed). Use it to prove that PKCE is
actually enforced on the client.

What it does:
  1. Generates a fresh code_verifier / code_challenge pair.
  2. Builds the /auth URL and opens it in your browser.
  3. Spins up a tiny local HTTP server on :8888 to catch the
     /callback redirect and pull out `code` + `state` automatically.
  4. Immediately exchanges the code for tokens (no copy/paste delay,
     so you don't hit expired/reused-code errors).
  5. Pretty-prints the token response.

Usage:
    python3 pkce-flow-negative-code_verifier.py

Edit KEYCLOAK_HOST / REALM / CLIENT_ID below if they differ.
"""

import secrets
import hashlib
import base64
import json
import webbrowser
import urllib.parse
import urllib.request
import http.server
import threading

# ---- config: adjust to match your setup ----
KEYCLOAK_HOST = "http://localhost:8080"
REALM = "lab1"
CLIENT_ID = "lab1-app"
REDIRECT_HOST = "localhost"   # must match "Valid redirect URIs" in Keycloak
REDIRECT_PORT = 8888
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"
SCOPE = "openid profile email"
STATE = secrets.token_urlsafe(8)
# ----------------------------------------------

AUTH_ENDPOINT = f"{KEYCLOAK_HOST}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_ENDPOINT = f"{KEYCLOAK_HOST}/realms/{REALM}/protocol/openid-connect/token"

# Step 1: generate PKCE pair
code_verifier = secrets.token_urlsafe(64)[:64]
digest = hashlib.sha256(code_verifier.encode()).digest()
code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

print("code_verifier :", code_verifier)
print("code_challenge:", code_challenge)
print()

# Step 2: build auth URL
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "state": STATE,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}
auth_url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
print("Opening browser for login:")
print(auth_url)
print()

# Step 3: tiny server to catch the callback
result = {}
done = threading.Event()


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence default request logging

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        qs = urllib.parse.parse_qs(parsed.query)
        result["code"] = qs.get("code", [None])[0]
        result["state"] = qs.get("state", [None])[0]
        result["error"] = qs.get("error", [None])[0]
        result["error_description"] = qs.get("error_description", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if result["code"]:
            self.wfile.write(b"<h2>Got the code. You can close this tab.</h2>")
        else:
            self.wfile.write(b"<h2>No code received - check the terminal.</h2>")

        done.set()


server = http.server.HTTPServer((REDIRECT_HOST, REDIRECT_PORT), CallbackHandler)
thread = threading.Thread(target=server.handle_request, daemon=True)
thread.start()

webbrowser.open(auth_url)
print(f"Waiting for callback on {REDIRECT_URI} ... (log in as alice in the browser)")

done.wait(timeout=120)
server.server_close()

if result.get("error"):
    print("\nAuthorization failed:", result["error"], "-", result.get("error_description"))
    raise SystemExit(1)

if not result.get("code"):
    print("\nTimed out waiting for the callback. Did the browser redirect to the right host/port?")
    raise SystemExit(1)

if result.get("state") != STATE:
    print("\nWARNING: state mismatch! Possible CSRF or stale request. Aborting.")
    raise SystemExit(1)

code = result["code"]
print("\nGot code:", code)
print("State verified OK.\n")

# --- NEGATIVE TEST: corrupt the verifier to test PKCE mismatch handling ---
code_verifier = code_verifier[:-1] + ("x" if code_verifier[-1] != "x" else "y")
print("Using WRONG code_verifier for this test:", code_verifier)
# ------------------------------------------------------------------

# Step 4: exchange the code immediately
token_data = urllib.parse.urlencode({
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "code": code,
    "redirect_uri": REDIRECT_URI,
    #"code_verifier": code_verifier,
}).encode()

req = urllib.request.Request(
    TOKEN_ENDPOINT,
    data=token_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
        print("Token endpoint response:")
        print(json.dumps(json.loads(body), indent=2))
except urllib.error.HTTPError as e:
    print("Token exchange failed:", e.code)
    print(e.read().decode())
