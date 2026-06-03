# UpContent + Sniply — Auth0 Demo

A teaching reference for real Auth0 patterns: PKCE SPA login, RS256/JWKS token
validation, and Management API orchestration from a trusted backend.
**DEMO — not for production.** Do not enter real credentials or protect real data.

Two branded SPAs share one identity backend: **UpContent** (Vue, :3001) and
**Sniply** (React, :3000). Both have full feature parity.

## Architecture

```
UpContent SPA (Vue   :3001) ─┐  PKCE → Auth0 Universal Login
Sniply    SPA (React :3000) ─┘  └─ user access token (aud = https://upcontent-api)
        │  Authorization: Bearer <access token>
        ▼
FastAPI resource server (:3003)
  • validate JWT (RS256 / JWKS, iss, aud, exp)
  • authorize: baseline token scope  +  per-org ownership (live check)
  • mint M2M Management token (cached) ──▶ Auth0 Management API v2
        ▼
Auth0 tenant (Universal Login, Organizations, RBAC) + Management API
```

## Run it

```bash
# Backend (FastAPI resource server) — port 3003
cd backend
cp .env.example .env     # set AUTH0_DOMAIN, AUTH0_MGMT_CLIENT_ID/_SECRET, AUTH0_SPA_CLIENT_ID
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
set -a && source .env && set +a
uvicorn app.main:app --host 127.0.0.1 --port 3003
# curl -s http://127.0.0.1:3003/healthz  →  {"status":"ok"}
pytest                   # validators + JWT validation (mocked JWKS)

# UpContent SPA (Vue) — port 3001
cd ../frontend-upcontent-vue && cp .env.example .env && npm install && npm run dev

# Sniply SPA (React) — port 3000
cd ../frontend-sniply-react && cp .env.example .env && npm install && npm run dev
```

Each frontend `.env` needs: `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID` (that
app's SPA client id), `VITE_AUTH0_AUDIENCE=https://upcontent-api`, and
`VITE_API_BASE_URL=http://127.0.0.1:3003`. All `VITE_*` values are public.

On either SPA: **Log in** → **Create** an organization (you become its owner) →
**Plans** (set a plan) → **Roles** (assign/remove) → **Invite** a teammate.

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

## Design decisions

- **Object-level per-org authorization.** Acting on a specific org (plan, invite,
  roles) is checked live server-side against the Management API ("is the caller an
  owner/admin of *this* org?"), not via a token scope. A freshly-granted role
  takes effect immediately — no token refresh or re-login.
- **Org-level plan metadata.** A selected plan is stored as organization metadata
  via the Management API (`PATCH /organizations/{id}`), not on the user — so it
  belongs to the account, not whoever set it.
- **Refresh-token-only renewal.** SPAs use rotating refresh tokens with reuse
  detection (`useRefreshTokens` + `offline_access`); no deprecated silent-iframe
  fallback. Tokens are never placed in URLs.
- **No database.** Auth0 is the system of record (users, orgs, roles, metadata).
  The backend is a stateless resource server that orchestrates the Management API.
- **Port :3003.** The resource server listens on 127.0.0.1:3003; the two SPAs run
  on :3001 (Vue) and :3000 (React) and are CORS-allowlisted explicitly (no `*`).

## Security notes

- **RS256 only**; `alg:none` / HS256 rejected; signature verified via JWKS; `iss`
  / `aud` / `exp` enforced; ID tokens and wrong-audience tokens rejected.
- **Auth0-id injection guard** — `org_id` / `user_id` / `role_id` are
  format-validated and URL-encoded before Management API use; malformed → **422**.
- **Strict CORS** (explicit allow-list), security headers, per-SPA CSP. M2M secret
  stays server-side and is never logged; clients get generic errors.

## Repo layout

```
upcontent-auth0-demo/
├── backend/                     FastAPI resource server (:3003)
│   ├── app/{main,security,config,tasks,mgmt_token,mgmt_service,validators,models}.py
│   ├── app/routes/{me,organizations,plans,roles}.py
│   └── tests/{test_validators,test_security}.py
├── frontend-upcontent-vue/      UpContent — Vite + Vue 3 + @auth0/auth0-vue (:3001)
├── frontend-sniply-react/       Sniply — Vite + React + @auth0/auth0-react (:3000)
├── setup/provision_auth0.py     optional Auth0 provisioning via the M2M
└── docs/                        handoff docs (see below)
```

## Continuing this project

- [`docs/GAP-ANALYSIS.md`](docs/GAP-ANALYSIS.md) — what is built vs. open, mapped
  to review feedback.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — prioritized backlog with acceptance
  criteria + the 3-step migration flow.
- [`docs/AUTH0-SETUP.md`](docs/AUTH0-SETUP.md) — tenant object map + a values
  checklist to stand up the tenant.
