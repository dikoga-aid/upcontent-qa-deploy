# UpContent + Sniply — Auth0 Demo

> **DEMO — not for production.** A teaching reference for Auth0 patterns. Do
> **not** enter real credentials or use it to protect real data.

This project demonstrates three things end to end:

1. **Securing a SPA and its API with Auth0** — the browser logs in with
   Authorization Code + PKCE and never holds a client secret; the API is an
   Auth0-protected resource server.
2. **Using JWT access tokens correctly** on both sides — the SPA acquires and
   sends them; the API validates them (signature, issuer, audience, expiry).
3. **Orchestrating the Auth0 Management API** from a trusted backend to compose
   real flows (create an organization, select a plan, invite a member, manage
   roles) using a machine-to-machine (M2M) credential.

Two branded single-page apps share one identity backend:

- **UpContent** — React + Vite, port **3000**
- **Sniply** — Vue 3 + Vite, port **3001**
- **Backend** — FastAPI, port **3003** — validates user access tokens
  (RS256/JWKS), authorizes each call, and calls the Management API via an M2M client.

```
UpContent SPA (React :3000) ─┐  PKCE → Auth0 Universal Login
Sniply    SPA (Vue   :3001) ─┘  └─ user access token (aud = https://upcontent-api)
        │  Authorization: Bearer <access token>
        ▼
FastAPI resource server (:3003)
  • validate JWT (RS256 / JWKS, iss, aud, exp)
  • authorize: baseline token scope  +  per-org ownership (live check)
  • mint M2M Management token (cached) ──▶ Auth0 Management API v2
```

## How the auth works

**Frontend (each SPA).** Uses `@auth0/auth0-react` / `@auth0/auth0-vue`
(Authorization Code + PKCE). It requests an access token for the API audience
(`https://upcontent-api`) and attaches it as `Authorization: Bearer …` on every
call. Tokens are renewed with **rotating refresh tokens** (`useRefreshTokens`,
`offline_access`) — the modern SPA approach; no deprecated silent-iframe
fallback. There are no cookies, so there is no CSRF surface.

**Backend (resource server).** Every `/api` request must carry a valid access
token. Validation (`app/security.py`): **RS256 only** (rejects `alg:none` and
HS256), signature checked against the tenant JWKS, and `iss` / `aud` / `exp`
verified — so ID tokens and tokens for other APIs are rejected.

**Two-layer authorization.**
- **Baseline token scopes** gate app-wide capability: `read:organization`
  (view your orgs) and `create:organization` (create one). These ride in the
  access token.
- **Per-org ownership** gates everything that acts on a specific organization
  (select plan, invite, manage roles). This is checked **live, server-side**
  against the Management API ("is the caller an owner/admin of *this* org?"),
  not via a token scope. Because it isn't in the token, a freshly-granted role
  takes effect immediately — **no token refresh or re-login**.

**Management API orchestration.** A backend M2M client mints a Management API
token via `client_credentials` (cached, auto-refreshed) and composes flows. For
example, **create organization** = create org → enable the database connection
(so invitations work) → add the creator as a member → assign the creator the
owner role. The M2M secret lives only in `backend/.env` and is never logged.

## API routes

| Method | Path | Token scope | Per-org check |
|---|---|---|---|
| GET  | `/api/me` | authenticated | — |
| GET  | `/api/plans` | authenticated | — |
| GET  | `/api/organizations` | `read:organization` | returns only your orgs |
| POST | `/api/organizations` | `create:organization` | — (you become owner) |
| POST | `/api/plan/select` | — | owner/admin of `org_id` |
| GET  | `/api/organizations/{org_id}/roles` | `read:organization` | member of org |
| POST | `/api/organizations/{org_id}/roles/assign` | — | owner/admin of org |
| POST | `/api/organizations/{org_id}/roles/remove` | — | owner/admin of org |
| POST | `/api/organizations/{org_id}/invitations` | — | owner/admin of org |
| GET  | `/healthz` | public | — |

"Owner/admin" = the caller holds a tenant role named (case-insensitive) `owner`,
`admin`, `org admin`, `organization admin`, or `upcnt_owner` **within that org**.
The create-org flow assigns the first such role it finds to the org's creator.

## Repo layout

```
upcontent-auth0-demo/
├── backend/                     FastAPI resource server
│   ├── app/
│   │   ├── main.py              app, CORS, security headers, routers, /healthz
│   │   ├── security.py          JWT validation + scope + per-org authz helpers
│   │   ├── mgmt_token.py        M2M client_credentials token (cached)
│   │   ├── mgmt_service.py      Management API client
│   │   ├── tasks.py             Management API flows (orchestration)
│   │   ├── validators.py        input + Auth0-id validation
│   │   ├── models.py            plans + request/response models
│   │   └── routes/{me,organizations,plans,roles}.py
│   ├── tests/{test_validators,test_security}.py
│   └── requirements.txt · .env.example
├── frontend-upcontent-react/    Vite + React + @auth0/auth0-react
├── frontend-sniply-vue/         Vite + Vue 3 + @auth0/auth0-vue
├── setup/provision_auth0.py     optional Auth0 provisioning via the M2M
└── README.md
```

## Auth0 configuration

**1. API (resource server).** Create an API with identifier `https://upcontent-api`,
RS256. Enable **RBAC** and **Add Permissions in the Access Token**. Define the
permissions: `read:organization`, `create:organization`, `update:organization`,
`invite:organizationUser`.

**2. Roles.** Grant `read:organization` + `create:organization` to all signed-in
users (e.g. a default role) — that's the app baseline. Create an **owner** role
(e.g. `upcnt_owner`) holding `update:organization` + `invite:organizationUser`;
the create-org flow assigns it per organization.

**3. SPA application.** Create a **Single Page Application** (Token Endpoint Auth
Method = None). Callback / Logout / Web Origins: `http://localhost:3000` and
`http://localhost:3001`. Enable **Refresh Token Rotation**. Enable
**Organizations** on the app (required for invitations). Put the **Client ID**
into each frontend's `.env` (`VITE_AUTH0_CLIENT_ID`) and `backend/.env`
(`AUTH0_SPA_CLIENT_ID`, used so invitation links target the SPA).

**4. M2M client (backend).** Authorize it for the Management API with these
scopes: `read:organizations`, `create:organizations`, `update:organizations`,
`create:organization_invitations`, `create:organization_members`,
`read:organization_members`, `read:organization_member_roles`,
`create:organization_member_roles`, `delete:organization_member_roles`,
`read:roles`, `read:connections`, `create:organization_connections`.

**5. Invitations** also require a **Default Login Route** (Tenant Settings →
Advanced) or an **Application Login URI** on the SPA app, so Auth0 can build the
invitation URL.

`setup/provision_auth0.py` can create the API / SPA app / roles automatically if
the M2M is authorized for `create:clients` / `create:resource_servers` / role
scopes; otherwise it prints the manual steps above.

## Run it

**Backend** (port 3003):
```bash
cd backend
cp .env.example .env     # set AUTH0_MGMT_CLIENT_ID/_SECRET and AUTH0_SPA_CLIENT_ID
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 3003
# curl -s http://127.0.0.1:3003/healthz  →  {"status":"ok"}
pytest                   # validators + JWT validation (mocked JWKS)
```

**Frontends:**
```bash
cd frontend-upcontent-react && cp .env.example .env && npm install && npm run dev   # :3000
cd ../frontend-sniply-vue   && cp .env.example .env && npm install && npm run dev   # :3001
```
Set `VITE_AUTH0_CLIENT_ID` (SPA client id) and `VITE_API_BASE_URL=http://127.0.0.1:3003`
in each frontend `.env`.

Then on a SPA: **Log in** → **Create** an organization (you become its owner) →
**Plans** (set a plan) → **Roles** (assign/remove) → **Invite** a teammate.

## Security notes

- **RS256 only**; `alg:none` / HS256 rejected; signature verified via JWKS; `iss`
  / `aud` / `exp` enforced; ID tokens and wrong-audience tokens rejected.
- **Per-org authorization** checked live against the Management API — scope alone
  never authorizes acting on a specific org.
- **Auth0-id injection guard** — `org_id` / `user_id` / `role_id` are
  format-validated and URL-encoded before use in Management API URLs; malformed
  values (e.g. `org_%2e%2e`) return **422**.
- **Refresh-token-only** renewal; tokens never placed in URLs; M2M secret stays
  server-side and is never logged; clients get generic errors.
- **Strict CORS** (explicit origin allow-list, no `*`), security headers, and a
  Content-Security-Policy on each SPA.
- **Rate limiting:** Management API calls (e.g. invitations) should be throttled
  in production to respect Auth0 limits — left out here to keep the focus on auth.
