# Deploy Change Log

Additive, append-only record of every config/environment/tenant change made
outside of the Git repo. Each entry is reversible and cross-referenced to the
card, branch, and commit that motivated it.

---

## 2026-06-19 — VOL-1: Invite a new user to an existing org

**Branch:** `feature/VOL-1-invite-user-existing-org`
**Card:** VOL-1
**Author:** Atacante (automated)

### Repo code changes (in PR — see GitHub)

| File | Change |
|---|---|
| `backend/app/models.py` | Added `role_ids: List[str]` to `InviteRequest` (Bug 2) |
| `backend/app/config.py` | `auth0_spa_client_id` made required (no default) — startup fails without it (AC 6) |
| `backend/app/mgmt_service.py` | `invite_user_to_organization` now accepts and forwards `role_ids` to Auth0 (Bug 2) |
| `backend/app/tasks.py` | `invite_member` accepts `role_ids`, validates each with `require_valid_role_id` (Bug 2) |
| `backend/app/routes/organizations.py` | Removed M2M fallback from `client_id` resolution; added email fallback for inviter name; passes `role_ids` to task (AC 6, inviter name spec) |
| `frontend-upcontent-vue/src/api.ts` | `invite()` now accepts `role_ids?: string[]` parameter (Bug 2) |
| `frontend-upcontent-vue/src/components/Organizations.vue` | Role selector added to invite dialog; roles loaded from API on org select (AC 1, Bug 2) |
| `frontend-upcontent-vue/src/App.vue` | `onMounted` handler detects `?invitation=&organization=` URL params and calls `loginWithRedirect` via auth0-vue SDK (Bug 7) |
| `frontend-upcontent-vue/index.html` | CSP `connect-src` backend origin now derived from `%VITE_API_BASE_URL%` and Auth0 domain from `%VITE_AUTH0_DOMAIN%` at Vite build time (Bug 6) |

### Auth0 tenant changes (QA — additive, reversible)

| Object | Change | Reversible? |
|---|---|---|
| UpContent SPA app (`Non4DMjqQ1dZK4uxXgg3u6i6Sb5Bt1Yg`) | Allowed Callback URL `https://upcontent-spa-qa.onrender.com` added | Yes — remove from list |
| UpContent SPA app | Allowed Logout URL `https://upcontent-spa-qa.onrender.com` added | Yes — remove from list |
| UpContent SPA app | Allowed Web Origin `https://upcontent-spa-qa.onrender.com` added | Yes — remove from list |
| Tenant | `default_redirection_uri` set to `https://upcontent-spa-qa.onrender.com` — required for invitation URL generation | Yes — unset or change value |

These tenant changes were applied during the live E2E reproduction run that
confirmed Bug 2, Bug 6, and Bug 7. See the Tech Spec (VOL-1) for the execution
evidence summary.

### Environment variables required at QA deploy (Render)

Backend (Render service: `upcontent-backend-qa`):
- `AUTH0_SPA_CLIENT_ID` = `Non4DMjqQ1dZK4uxXgg3u6i6Sb5Bt1Yg` (SPA client, not M2M) — **NEW required var** (previously optional with M2M fallback; fallback removed)

Frontend (Render static site: `upcontent-spa-qa`):
- `VITE_API_BASE_URL` = `https://upcontent-backend-qa.onrender.com` — **existing var, now also controls CSP connect-src at build time**
- `VITE_AUTH0_DOMAIN` = `dev-rvvkxpvy18wueufd.us.auth0.com` — **existing var, now also controls CSP connect-src at build time**

No new secrets introduced. `AUTH0_SPA_CLIENT_ID` is the public SPA client ID
(not a secret — it is already embedded in the SPA bundle via `VITE_AUTH0_CLIENT_ID`).
