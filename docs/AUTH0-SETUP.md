# Auth0 Setup

What to stand up in the Auth0 tenant to run this demo, and the values to set.
All `VITE_*` values are public (shipped to the browser); only the M2M secret is
sensitive and lives in `backend/.env` only.

## Tenant object map

```
Auth0 tenant
│
├── API (resource server)
│     identifier / audience: https://upcontent-api
│     signing: RS256   RBAC: on   "Add Permissions in Access Token": on
│     permissions: read:organization, create:organization,
│                  update:organization, invite:organizationUser
│
├── SPA app — UpContent (Vue)            ├── SPA app — Sniply (React)
│     type: Single Page App              │     type: Single Page App
│     token endpoint auth: None          │     token endpoint auth: None
│     callbacks/origins:                 │     callbacks/origins:
│       http://localhost:3001            │       http://localhost:3000
│     refresh token rotation: on         │     refresh token rotation: on
│     Organizations: enabled             │     Organizations: enabled
│     (this is AUTH0_SPA_CLIENT_ID,      │     social: Google / Twitter /
│      the invite-link target)           │       Facebook / Buffer (roadmap #16)
│
├── Roles (RBAC)
│     baseline (all users): read:organization, create:organization
│     upcnt_owner: update:organization, invite:organizationUser
│                  (assigned per-org by the create-org flow)
│
├── M2M app (backend) ── client_credentials ──► Management API v2
│     holds the 12 Management scopes (below); secret in backend/.env only
│
└── Tenant settings
      Default Login Route (required for invitation URLs)
      Consent: first-party disabled, third-party enabled (#9)
      Attack Protection: bot / brute-force / breached-password (#15)
      Log stream → DataDog (#7)
```

## Values checklist

- **API**: identifier `https://upcontent-api`, RS256, RBAC on, "Add Permissions
  in Access Token" on; permissions `read:organization`, `create:organization`,
  `update:organization`, `invite:organizationUser`.
- **SPA callbacks / logout / web origins**:
  - UpContent (Vue): `http://localhost:3001`
  - Sniply (React): `http://localhost:3000`
- **Refresh token rotation**: enabled on both SPA apps (reuse detection on).
- **Organizations**: enabled on both SPA apps; set a **Default Login Route**
  (Tenant Settings → Advanced) or an Application Login URI so Auth0 can build the
  invitation URL.
- **Roles**: baseline role with `read:organization` + `create:organization` for
  all signed-in users; `upcnt_owner` with `update:organization` +
  `invite:organizationUser`, assigned per-org by the create-org flow.
- **M2M scopes (12)** for the Management API:
  `read:organizations`, `create:organizations`, `update:organizations`,
  `create:organization_invitations`, `create:organization_members`,
  `read:organization_members`, `read:organization_member_roles`,
  `create:organization_member_roles`, `delete:organization_member_roles`,
  `read:roles`, `read:connections`, `create:organization_connections`.
- **Social connections** (Sniply, roadmap): Google, Twitter, Facebook, Buffer.
- **Consent**: first-party disabled, third-party enabled (per app).
- **Attack Protection**: bot detection, brute-force protection, breached-password
  detection enabled.
- **Log stream**: tenant → DataDog (or SIEM).

## Where the values go

| Auth0 value | Set in |
|---|---|
| Tenant domain | `backend/.env` `AUTH0_DOMAIN`; each SPA `.env` `VITE_AUTH0_DOMAIN` |
| API audience | `backend/.env` `AUTH0_API_AUDIENCE`; each SPA `VITE_AUTH0_AUDIENCE` |
| UpContent SPA client id | `frontend-upcontent-vue/.env` `VITE_AUTH0_CLIENT_ID`; `backend/.env` `AUTH0_SPA_CLIENT_ID` (invite-link target) |
| Sniply SPA client id | `frontend-sniply-react/.env` `VITE_AUTH0_CLIENT_ID` |
| M2M client id / secret | `backend/.env` `AUTH0_MGMT_CLIENT_ID` / `AUTH0_MGMT_CLIENT_SECRET` (server-side only) |

`setup/provision_auth0.py` can create the API / SPA apps / roles automatically if
the M2M is authorized for `create:clients` / `create:resource_servers` / role
scopes; otherwise it prints the manual steps.
