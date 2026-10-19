# OAuth 2.0 / OIDC with Keycloak (local lab)

Hands-on lab: Authorization Code + PKCE (with a negative test) and Client Credentials against a local Keycloak in Docker, used AI for script generation.

**Step 1: Run Keycloak in Docker** and create keycloak.env.

```bash
docker run -d --name keycloak -p 8080:8080 --env-file keycloak.env -v keycloak_data:/opt/keycloak/data quay.io/keycloak/keycloak:latest start-dev
```

```
KEYCLOAK_ADMIN=<admin-username>
KEYCLOAK_ADMIN_PASSWORD=<choose-a-password>
```

**Step 2: Create a realm**
- Admin console → top-left realm dropdown → **Create realm**
- Name it `lab1` → Create.

**Step 3: Create a test user**
- Left menu → **Users** → **Add user**
  - Username: `username`
  - Email verified: On
  - Create
- Go to the **Credentials** tab for `username` → **Set password** → turn OFF "Temporary" → Save.

**Step 4: Create a public client with PKCE enforced**
- Left menu → **Clients** → **Create client**
  - Client ID: `lab1-app`
  - Client type: OpenID Connect → Next
  - Client authentication: **OFF** (this makes it a public client, correct for Auth Code + PKCE without a client secret)
  - Standard flow: **ON** (this is Authorization Code)
  - Direct access grants: OFF (not needed for this lab)
  - Next → Save
- Open the client → **Settings** tab:
 - Valid redirect URIs: `http://localhost:8888/callback`
  - Web origins: `http://localhost:8888`
  - Save
- Go to **Advanced** tab → scroll to **Proof Key for Code Exchange Code Challenge Method** → set to `S256` → Save.
  This forces Keycloak to reject the flow if you don't send a correct PKCE challenge — exactly what you want for this lab.
## Generate the PKCE pair yourself / Drive the Authorization Code flow manually

PKCE needs a random `code_verifier` and a `code_challenge` = base64url(SHA256(code_verifier)).

**Step 5: Run pkce-flow.py which will generate them and will build  the authorization URL with filled code_challenge*** ( script is used due manual copy/paste delay and expired/reused-code errors )
Authorization URL:
```
http://localhost:8080/realms/lab1/protocol/openid-connect/auth?
  response_type=code
  &client_id=lab1-app
  &redirect_uri=http://localhost:8888/callback
  &scope=openid profile email
  &state=xyz123
  &code_challenge=<YOUR_CODE_CHALLENGE>
  &code_challenge_method=S256
```

Paste the URL into a browser. Log in as related user, the script will copy `code` value from the callback redirect and will confirm the `state` matches what you sent ( CSRF check a real app must do). Also will exchange the code for tokens.

```shell
curl -X POST http://localhost:8080/realms/lab1/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=lab1-app" \
  -d "code=<CODE_FROM_REDIRECTED_URL" \
  -d "redirect_uri=http://localhost:8888/callback" \
  -d "code_verifier=<YOUR_CODE_VERIFIER>"
```

Should get back JSON with `access_token`, `id_token`, and `refresh_token`.

**Negative test (PKCE must be enforced):** run `python3 pkce-flow-negative-code_verifier.py`. It performs the same login but sends a corrupted/missing `code_verifier`, so Keycloak should reject the token exchange with an `invalid_grant` error. If you still get tokens back, PKCE is not enforced on the client; re-check the **Advanced** tab setting from Step 4.
## Verify the token yourself (no library)
Decode the ID token -> Paste the `id_token` into https://jwt.io

##  Client Credentials flow (machine-to-machine)

**Create a second, confidential client**
- Clients → Create client → Client ID: `lab1-service`
- Client authentication: **ON** (confidential client, gets a secret)
- Standard flow: OFF, Secrvice accounts roles: **ON**
- Save → go to **Credentials** tab → copy the client secret.

**Get a token with no user involved**
```bash
curl -X POST http://localhost:8080/realms/lab1/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=lab1-service" \
  -d "client_secret=<CLIENT_SECRET_HERE>"
```
