# UpContent + Sniply - Auth0 Demo (token-based microservices)

> **DEMO - not for production.** This project is a teaching/demonstration
> reference for Auth0 patterns. It is **not** a production system. Do **not**
> enter real credentials or rely on it to protect real data. (This disclaimer
> mirrors the "not for production" note carried by the `siaa-auth0-demo` and
> `twia-auth0-demo` references.)

Two branded single-page apps share one Auth0-protected identity backend:

- **UpContent** (React + Vite, port **3000**) - content-curation product.
- **Sniply** (Vue 3 + Vite, port **3001**) - link-shortener-with-CTA product.
- **Backend** (FastAPI, port **5000**) - an Auth0-protected **resource
  server** that validates user access tokens (RS256/JWKS), enforces per-route
  RBAC scopes **and** per-org object-level authorization, and performs
  privileged Auth0 Management API operations using a server-side M2M client.

```
UpContent SPA (React :3000) ─┐  PKCE → Auth0 Universal Login
Sniply    SPA (Vue   :3001) ─┘  └─ user access token (aud=https://upcontent-api)
        │  Authorization: Bearer <user access token>
        ▼
FastAPI resource server (:5000)
  • validate JWT (RS256/JWKS, iss, aud)  • per-route scope  • per-org membership/admin
  • mint M2M Management token (cached) ──▶ Auth0 Management API v2
```

Two tokens, two authz layers: the **user token** (RBAC permissions) authorizes
SPA → API; the **M2M token** (server-only) authorizes API → Management API.
No cookies, so no CSRF; security rests on Bearer + strict CORS + object-level
checks. The browser holds the access token **in memory only** (never
localStorage) with rotating refresh tokens.

## Repo layout

```
upcontent-auth0-demo/
├── backend/                     FastAPI resource server
│   ├── app/{main,config,security,mgmt_token,mgmt_service,tasks,validators,models}.py
│   ├── app/routes/{me,organizations,plans,roles}.py
│   ├── tests/{test_validators,test_security}.py
│   ├── requirements.txt  ·  .env.example
├── frontend-upcontent-react/    Vite + React + TS + @auth0/auth0-react
├── frontend-sniply-vue/         Vite + Vue 3 + TS + @auth0/auth0-vue
├── setup/provision_auth0.py     Idempotent Auth0 provisioning (M2M)
└── README.md
```

## API routes (each enforces a user-token scope AND, where applicable, an object check)

| Method | Path | Scope | Object check |
|---|---|---|---|
| GET  | `/api/me` | authenticated | - |
| GET  | `/api/plans` | authenticated | - |
| GET  | `/api/organizations` | `read:organizations` | results filtered to caller's orgs |
| POST | `/api/organizations` | `create:organizations` | - (creator) |
| POST | `/api/plan/select` | `update:organizations` | caller is member of `org_id` |
| POST | `/api/organizations/{org_id}/invitations` | `create:organization_invitations` | caller admin of org |
| GET  | `/api/organizations/{org_id}/roles` | `read:organization_members` | caller member of org |
| POST | `/api/organizations/{org_id}/roles/assign` | `create:organization_member_roles` | caller admin of org |
| POST | `/api/organizations/{org_id}/roles/remove` | `delete:organization_member_roles` | caller admin of org |
| GET  | `/healthz` | public | - |

"Admin" means the caller holds a tenant role named "Org Admin"/"Admin"
(case-insensitive) within that organization.

## Prerequisites

- Python 3.9+ and Node 18+.
- The running Auth0 tenant `dev-rvvkxpvy18wueufd.us.auth0.com` and its M2M
  client (already authorized for the Management API org/role scopes).

## 1. Auth0 configuration

You can attempt automatic provisioning, but the existing M2M client in this
tenant is **not** authorized for `create:clients` / `create:resource_servers`
/ role-creation scopes, so the steps below must currently be done **manually**
in the Auth0 Dashboard. (The script detects the 403 and prints these same
steps; re-run it after granting the scopes and it becomes a no-op.)

```bash
cd backend && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python ../setup/provision_auth0.py     # prints manual steps if not authorized
```

### Manual Dashboard steps

1. **APIs → Create API**
   - Name: `UpContent + Sniply API`
   - Identifier (audience): `https://upcontent-api`
   - Signing algorithm: **RS256**
   - In the API Settings, enable **RBAC**, **Add Permissions in the Access
     Token**, and **Allow Offline Access**.
   - In the API **Permissions** tab, add: `read:organizations`,
     `create:organizations`, `update:organizations`,
     `create:organization_invitations`, `read:organization_members`,
     `create:organization_member_roles`, `delete:organization_member_roles`.

2. **Applications → Create Application → "Single Page Web Applications"**
   - Name: `UpContent + Sniply SPA` (one SPA app shared by both frontends).
   - Token Endpoint Authentication Method: **None** (public PKCE client).
   - Allowed Callback URLs: `http://localhost:3000, http://localhost:3001`
   - Allowed Logout URLs: `http://localhost:3000, http://localhost:3001`
   - Allowed Web Origins: `http://localhost:3000, http://localhost:3001`
   - In **Refresh Token Rotation**, enable **Rotation** (this turns on
     automatic reuse detection) and **Absolute Expiration**.
   - Copy the **Client ID** into both frontends' `.env`
     (`VITE_AUTH0_CLIENT_ID`) and into `backend/.env` (`AUTH0_SPA_CLIENT_ID`,
     used so invitation links target the SPA).

3. **User Management → Roles → Create Role**
   - `Org Admin` - add **all** the permissions above.
   - `Member` - add `read:organizations`, `read:organization_members`.
   - Assign roles to your test users so their access tokens carry permissions.
     (The backend reads RBAC from both the `permissions` array and the `scope`
     string.)

### M2M (server-side) scopes

The backend's M2M client must hold these Management API scopes (least
privilege): `read:organizations`, `create:organizations`,
`update:organizations`, `create:organization_invitations`,
`read:organization_members`, `read:organization_member_roles`,
`create:organization_member_roles`, `delete:organization_member_roles`,
`read:roles`, `read:connections`, `create:organization_connections`.

## 2. Run the backend

```bash
cd backend
cp .env.example .env        # then fill AUTH0_MGMT_CLIENT_ID / _SECRET, AUTH0_SPA_CLIENT_ID
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 5000
# health check:  curl -s http://127.0.0.1:5000/healthz   →  {"status":"ok"}
```

> On macOS, AirPlay Receiver also listens on port 5000 (`*:5000`). Use
> `127.0.0.1:5000` explicitly, or disable AirPlay Receiver in System Settings,
> or set `PORT` to another value.

Run tests: `cd backend && . .venv/bin/activate && pytest`.

## 3. Run the frontends

```bash
cd frontend-upcontent-react
cp .env.example .env        # set VITE_AUTH0_CLIENT_ID to your SPA client_id
npm install && npm run dev  # http://localhost:3000

cd ../frontend-sniply-vue
cp .env.example .env        # same VITE_AUTH0_CLIENT_ID
npm install && npm run dev  # http://localhost:3001
```

## Security model (implemented)

1. **RS256 only** - `alg:none` and HS256 are rejected (no algorithm
   confusion); signature verified against the tenant JWKS (`PyJWKClient`,
   cached).
2. `iss`/`aud` verified; `exp`/`nbf` with <=60s leeway. ID tokens (audience =
   SPA client_id) are rejected - the audience must be `https://upcontent-api`.
3. **Object-level authorization** - scope alone is insufficient: every
   org-scoped mutation verifies membership (and admin, for role/invite changes)
   via the Management API; `GET /api/organizations` returns only the caller's
   orgs.
4. **Path-param injection / SSRF guard** - `org_id` / `user_id` / `role_id` are
   format-validated (`^org_...$`, Auth0 user-id shape, `^rol_...$`) and
   URL-encoded before interpolation into Management API URLs. Malformed values
   (e.g. `org_%2e%2e`) return **422**.
5. **In-memory tokens + strict CSP** - `cacheLocation="memory"`,
   `useRefreshTokens=true`; each SPA ships a strict Content-Security-Policy
   (`<meta>` in `index.html`) limiting `script-src` to self and `connect-src`
   to the API + Auth0 domain.
6. **Strict CORS** - explicit two-origin allow-list; no `*`, no credentials.
7. **Security headers** - `Cache-Control: no-store`, `X-Content-Type-Options:
   nosniff`, `Referrer-Policy: no-referrer`, HSTS when `PRODUCTION=true`.
8. **Least privilege** - SPA requests only the scopes it needs; M2M keeps only
   its Management scopes (documented above).
9. **Secret & log hygiene** - the M2M secret lives only in `backend/.env`, is
   never logged; user input is sanitized in error messages; clients get
   generic errors while details are logged server-side.
10. **Abuse control** - a lightweight in-memory rate limit on
    `POST .../invitations` (5 / 60s per caller).
11. **Federated logout** - `logout({ logoutParams: { returnTo } })`.

## Manual verification steps (finish the interactive flow)

The non-interactive checks below were verified automatically. The full OAuth
login uses Auth0 Universal Login (real user credentials) and must be completed
by a human on **both** SPAs:

1. Complete the Auth0 configuration above; assign the `Org Admin` role to your
   test user.
2. Start the backend (:5000) and both SPAs (:3000, :3001).
3. On each SPA: click **Log in** → complete PKCE login → land back on the
   branded DEMO page.
4. **Portal** shows your profile and the permissions carried by your token.
5. **Organizations**: create an organization (the backend auto-enables the DB
   connection so invitations work), then list it.
6. **Plans**: pick a plan; the org's plan badge updates (stored in org
   metadata).
7. **Organizations → invite**: invite an email; confirm in Auth0 Logs /
   the invitee's inbox.
8. **Roles**: assign then remove a role for a member; confirm via Auth0.
9. Negative checks: a user without the `Org Admin` role gets **403** on
   assign/remove/invite; acting on an org you are not a member of gets **403**.

## What was verified automatically

- Backend: venv + install + `uvicorn`; `GET /healthz` → 200.
- `pytest` → green (validators + JWT validation with a mocked JWKS, including
  RS256-only, wrong issuer/audience, expiry, HS256 / `alg:none` rejection,
  scope enforcement, and `permissions`-array merging).
- No token → **401**; malformed `{org_id}` (`org_%2e%2e`) → **422**.
- Both SPAs `npm run build` (type-checked) and `npm run dev`; landing pages
  render their brand + DEMO banner/ribbon (verified visually).
- Auth0 provisioning script runs and degrades gracefully (the current M2M
  client lacks provisioning scopes; the script prints the manual steps).
```
