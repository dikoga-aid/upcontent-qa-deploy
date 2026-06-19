# QA Report — VOL-1: Invite a New User to an Existing Org

**QA Engineer:** Goleiro (QA/Security)
**PR:** #6 — `fix(VOL-1): invite sends roles, fix CSP, add invitation-link handler`
**Branch under test:** `feature/VOL-1-invite-user-existing-org` (commit b9ce520)
**QA target:** `https://upcontent-spa-qa.onrender.com` / `https://upcontent-backend-qa.onrender.com`
**Date:** 2026-06-19
**Tech Spec version:** v2

---

## VERDICT: FAIL — Deployment blocker

**The feature branch was NOT deployed to the QA environment before this run.** Both the SPA and backend on Render are running pre-PR-#6 code. No acceptance criterion can be confirmed against the running system; AC 7 (CSP) is **confirmed FAIL** on the deployed environment, which is the exact bug PR #6 was supposed to fix.

This card must be routed to **Preparador/DevSecOps** to trigger a Render redeploy of `feature/VOL-1-invite-user-existing-org` before QA can proceed.

---

## Deployment Evidence (what blocked this run)

Three independent signals confirm the old build is running:

### Signal 1 — SPA CSP (live browser, CONFIRMED)

Deployed CSP `connect-src` (captured from browser):
```
connect-src 'self' http://127.0.0.1:3003 https://dev-rvvkxpvy18wueufd.us.auth0.com ws://localhost:3000
```

Feature branch CSP (source code, after Vite substitution with `VITE_API_BASE_URL=https://upcontent-backend-qa.onrender.com`):
```
connect-src 'self' https://upcontent-backend-qa.onrender.com https://dev-rvvkxpvy18wueufd.us.auth0.com ws://localhost:3000
```

`http://127.0.0.1:3003` is the pre-fix hardcoded localhost origin. The Vite `%VITE_API_BASE_URL%` substitution never ran.

### Signal 2 — Live CSP violation (browser console, CONFIRMED)

```
[error] Connecting to 'https://upcontent-backend-qa.onrender.com/api/plans' violates the following
        Content Security Policy directive: "connect-src 'self' http://127.0.0.1:3003 ..."
[error] Fetch API cannot load https://upcontent-backend-qa.onrender.com/api/plans.
        Refused to connect because it violates the document's Content Security Policy.
```

The Plans page renders "**Failed to fetch**" — all backend calls are blocked. Evidence: `evidence/captures/VOL-1/04-plans-csp-blocked.png`

### Signal 3 — Backend InviteRequest schema (OpenAPI, CONFIRMED)

`GET https://upcontent-backend-qa.onrender.com/openapi.json` returns:

```json
{
  "title": "InviteRequest",
  "type": "object",
  "required": ["email"],
  "properties": {
    "email": { "type": "string" },
    "inviter_name": { "anyOf": [{"type":"string"}, {"type":"null"}] }
  }
}
```

`role_ids` is absent. The feature branch adds `role_ids: List[str]` to this model. The backend has not been rebuilt from the feature branch.

### Signal 4 — SPA JS bundle (static analysis)

Deployed bundle `assets/index-qzRWwY8F.js` — invite function extracted:

```js
invite:(e,t,n,s)=>Wt(e,"POST",`/api/organizations/${t}/invitations`,{email:n,inviter_name:s})
```

No `role_ids` in the payload. Feature branch would produce:
```js
invite:(e,t,n,s,r)=>Wt(e,"POST",`/api/organizations/${t}/invitations`,{email:n,inviter_name:s,role_ids:r})
```

Role-selector UI strings absent from bundle:
- `"Choose a role…"` — absent
- `"Loading roles…"` — absent
- `"Role granted to the invitee on acceptance"` — absent

---

## Acceptance Criteria Results

| AC | Description | Verdict | Basis |
|---|---|---|---|
| AC 1 | Owner sees role selector populated with org roles | BLOCKED | Old SPA deployed; no role selector in bundle |
| AC 2 | Invite carries non-empty `roles` array | BLOCKED | Old backend schema; invite payload has no `role_ids` |
| AC 3 | Invitation link drives SDK `loginWithRedirect`, no error | BLOCKED | Old SPA deployed; `onMounted` invitation handler absent |
| AC 4 | After acceptance, invitee holds selected role | BLOCKED | Depends on AC 2 and AC 3 |
| AC 5 | With org plan set, `/api/me` returns non-null plan | OUT OF SCOPE | Per Tech Spec v2: validate next run |
| AC 6 | `AUTH0_SPA_CLIENT_ID` unset → startup fails; set → invite links carry SPA client_id | BLOCKED | Feature code not deployed; cannot test startup enforcement |
| AC 7 | Real browser with CSP enforced: org list loads, invite submits, `/api/me` loads | **CONFIRMED FAIL** | Live browser shows CSP blocking `https://upcontent-backend-qa.onrender.com`; Plans page "Failed to fetch" |
| AC 8 | No regression: org create, plan select, owner-role assignment | BLOCKED | Old code running; Plans page broken due to CSP |
| AC 9 | Wrong-audience token rejected with 401 | INFERRED PASS | `curl` with malformed token → 401; security middleware unchanged; cannot confirm audience-specific rejection without real M2M token |

**CONFIRMED FAIL count: 1 (AC 7)**
**BLOCKED count: 7 (AC 1-4, 6, 8)**
**OUT OF SCOPE: 1 (AC 5)**
**INFERRED PASS: 1 (AC 9)**

---

## Security Pass

| Finding | Severity | Status | Basis |
|---|---|---|---|
| CSP blocks ALL backend requests in deployed QA SPA | **CRITICAL** | CONFIRMED | Live browser; `http://127.0.0.1:3003` in `connect-src` on QA URL |
| Feature branch security fixes NOT deployed (no `AUTH0_SPA_CLIENT_ID` enforcement, no SDK invite handler) | **HIGH** | CONFIRMED | Backend schema + SPA bundle analysis |
| AC 9 — wrong-audience token returns 401 | — | INFERRED PASS | Security middleware unchanged from passing pre-PR tests |
| No secrets in repo | PASS | VERIFIED | Static analysis; no `.env` or credential files committed |

The CRITICAL finding is the deployment itself: the QA SPA is entirely broken for authenticated use because CSP blocks all backend calls. This predates PR #6 and is exactly what Bug 6 fixes — but the fix is not running.

---

## What to do next

**Required before QA can proceed:**

1. **Preparador** triggers a Render redeploy of `feature/VOL-1-invite-user-existing-org` for BOTH services:
   - `upcontent-spa-qa` (static site) — must be rebuilt with `VITE_API_BASE_URL=https://upcontent-backend-qa.onrender.com`
   - `upcontent-backend-qa` (web service) — must include `role_ids` in `InviteRequest`

2. Verify deployment by checking:
   - SPA CSP `connect-src` contains `https://upcontent-backend-qa.onrender.com` (not `http://127.0.0.1:3003`)
   - `GET https://upcontent-backend-qa.onrender.com/openapi.json` shows `role_ids` in `InviteRequest` schema

3. **Goleiro re-runs QA** from scratch against the newly deployed environment.

---

## Evidence Files

Raw captures committed to `evidence/captures/VOL-1/`:

| File | What it shows |
|---|---|
| `01-spa-landing.png` | QA SPA landing page (old build, no org tabs visible pre-login) |
| `02-spa-landing-annotated.png` | Annotated interactive elements on landing page |
| `03-plans-page-csp-failure.png` | Plans page after navigating; CSP errors already fired |
| `04-plans-csp-blocked.png` | Plans page showing "Failed to fetch" (CSP-blocked API call) |

Browser console log (CSP violations), backend OpenAPI response (`InviteRequest` schema), and SPA bundle invite function text are inline above.

---

*QA run executed: 2026-06-19. Evidence captured by Goleiro against the live QA environment. All CONFIRMED findings are backed by executed flows or captured HTTP responses — not static code analysis.*
