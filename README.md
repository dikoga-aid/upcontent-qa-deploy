# UpContent + Sniply — Auth0 Demo

A teaching reference for real Auth0 patterns: PKCE SPA login, RS256/JWKS token
validation, and Management API orchestration from a trusted backend.
**DEMO — not for production.** Do not enter real credentials or protect real data.

Two branded SPAs share one identity backend, each with its own Auth0 client and
API audience: **UpContent** (Vue, :3000) is the full org/plan/role management
app; **Sniply** (React, :3001) is a focused login + profile demo. The split
illustrates per-app audiences and scopes - Sniply requests no org scopes and
reads its org/role/plan context straight from the token (the post-login action
stamps it), so it never calls the Management API.

## Architecture

```
UpContent SPA (Vue   :3000) ─┐  PKCE → Auth0 Universal Login
Sniply    SPA (React :3001) ─┘  └─ user access token
        │   (aud = https://upcontent-api  |  https://sniply-api)
        │  Authorization: Bearer <access token>
        ▼
FastAPI resource server (:3003)
  • validate JWT (RS256 / JWKS, iss, aud, exp); accepts either app audience
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

# UpContent SPA (Vue) — port 3000
cd ../frontend-upcontent-vue && cp .env.example .env && npm install && npm run dev

# Sniply SPA (React) — port 3001
cd ../frontend-sniply-react && cp .env.example .env && npm install && npm run dev
```

### Environment / client map

Each app authenticates with its own Auth0 client and requests its own API
audience. Wire the env values to these Auth0 objects (SPA client ids are public;
the M2M secret is server-side only):

| Env var | Auth0 object | Used by |
|---|---|---|
| `frontend-upcontent-vue` → `VITE_AUTH0_CLIENT_ID` | `UpContent SPA` (SPA, auth=none) | UpContent SPA :3000 |
| `frontend-upcontent-vue` → `VITE_AUTH0_AUDIENCE` | `https://upcontent-api` | UpContent token audience |
| `frontend-sniply-react` → `VITE_AUTH0_CLIENT_ID` | `Sniply` (SPA, auth=none) | Sniply SPA :3001 |
| `frontend-sniply-react` → `VITE_AUTH0_AUDIENCE` | `https://sniply-api` | Sniply token audience |
| `backend` → `AUTH0_MGMT_CLIENT_ID` / `_SECRET` | `UpC Services - MGM API` (M2M) | backend → Management API v2 |
| `backend` → `AUTH0_SPA_CLIENT_ID` | `UpContent SPA` | invitation link target |
| `backend` → `AUTH0_API_AUDIENCE` | `https://upcontent-api,https://sniply-api` | audiences the API accepts |

All `VITE_*` values are public (shipped to the browser). The backend accepts
either audience, so both SPAs call the one resource server on
`VITE_API_BASE_URL=http://127.0.0.1:3003`.

> Each SPA's `index.html` Content-Security-Policy lists the Auth0 tenant host in
> `connect-src` (the `/oauth/token` code-exchange and refresh-token rotation
> calls); replace the placeholder `your-tenant.us.auth0.com` with your own tenant
> domain. Login is a full-page redirect and the SPAs renew via rotating refresh
> tokens, so no silent-auth iframe is used (`default-src 'self'` already blocks
> framing).

**UpContent**, logged out: browse the public **Plans** pricing page and **Sign
up for** a plan. This simulates a separate marketing site initiating signup: the
plan is sent to Auth0 as the `selected-plan` Authorize parameter; the post-login
Action (**Add Custom Claims**) reads it and stamps a `https://upcontent.com/pending_plan`
token claim, and the backend applies that to the organization you create - a real
round-trip through Auth0, nothing pre-stored locally. After signing in: **Create**
an organization (you become its owner; a plan chosen at signup is applied to it
automatically) → **Plans** (set/change the plan) → **Roles** (assign/remove) →
**Invite** a teammate.

**Sniply** is login + profile only: sign in, and the profile shows the org,
role, and plan carried in your token (no org management).

## API

The two layers are kept distinct: the SPA talks to the backend over these HTTP
endpoints, and the backend (and only the backend) talks to the Auth0 Management
API v2 using its M2M token.

### SPA → backend (resource server)

UpContent uses all of these; **Sniply only calls `GET /api/me`** (plus the public
`GET /api/plans` for its landing teaser), since it does no org management.

| Method | Path | Authorization |
|---|---|---|
| GET  | `/api/me` | any valid token (returns identity + org/role/plan from token claims) |
| GET  | `/api/plans` | public (catalog drives the logged-out pricing page) |
| GET  | `/api/organizations` | token scope `read:organization` |
| POST | `/api/organizations` | token scope `create:organization` |
| POST | `/api/plan/select` | owner/admin of `org_id` (object-level) |
| GET  | `/api/organizations/{org_id}/roles` | member of org + `read:organization` |
| POST | `/api/organizations/{org_id}/roles/assign` | owner/admin of org (object-level) |
| POST | `/api/organizations/{org_id}/roles/remove` | owner/admin of org (object-level) |
| POST | `/api/organizations/{org_id}/invitations` | owner/admin of org (object-level) |
| GET  | `/healthz` | public |

### backend → Auth0 Management API v2

Each SPA endpoint composes one or more Management API calls (the SPA never calls
Auth0 directly):

| SPA endpoint | Management API calls |
|---|---|
| `GET /api/organizations` | `GET /users/{id}/organizations`, then `GET /organizations/{id}` per org (plan metadata) |
| `POST /api/organizations` | `POST /organizations` → `POST /organizations/{id}/members` → `GET /roles` → `POST /organizations/{id}/members/{user}/roles` |
| `POST /api/plan/select` | membership/role check, then `PATCH /organizations/{id}` (writes `metadata.selected_plan`) |
| `GET /api/organizations/{id}/roles` | `GET /organizations/{id}/members` (+ `GET .../members/{user}/roles` each), `GET /roles` |
| `POST .../roles/assign` \| `.../roles/remove` | `POST` \| `DELETE /organizations/{id}/members/{user}/roles` |
| `POST .../invitations` | `POST /organizations/{id}/invitations` |

Authorization is **object-level**: acting on a specific org is checked live
against the Management API ("is the caller a member / owner/admin of *this*
org?"), so a freshly granted role takes effect immediately with no token refresh.
"Owner/admin" = the caller holds a tenant role named (case-insensitive) `owner`,
`admin`, `org admin`, `organization admin`, or `upcnt_owner` **within that org**.

**Owner uniqueness.** Per the A&D, an organization has exactly **one owner**.
Auth0 cannot model this constraint, so the **app enforces it**: the create-org
flow makes the creator the owner, and assigning an owner role
(`POST .../roles/assign`) first checks the org's members via the Management API
and rejects (HTTP 409) if a *different* member already holds an owner role;
ownership must be removed/transferred first.

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
│   └── app/routes/{me,organizations,plans,roles}.py
├── frontend-upcontent-vue/      UpContent — Vite + Vue 3 + @auth0/auth0-vue (:3000)
└── frontend-sniply-react/       Sniply — Vite + React + @auth0/auth0-react (:3001)
```
