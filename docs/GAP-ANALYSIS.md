# Gap Analysis (verified)

Verified **2026-06-04** against the live tenant export (`a0deploy export`, re-pulled after
a tenant cleanup), the repo code, and the A&D v2. Status: ✅ done · ◐ partial · ✗ not started · ⚠️ inconsistent.
"#" references the 2026-05-22 review. Paraphrased - see the (confidential) A&D for detail.

**2026-06-04 update:** shipped **Self-Registration → Selecting a Plan** as a real Auth0
round-trip - the pricing page sends `selected-plan` to `/authorize`; the post-login
**Add Custom Claims** Action (updated + **bound to post-login** via the Management API) stamps a
`pending_plan` token claim; `POST /api/organizations` reads the claim and writes
`org.metadata.selected_plan` server-side (no localStorage). Made `GET /api/plans` public and set
`organization_usage=allow`. Also shipped: **owner 1:1 uniqueness enforced server-side** (creator
becomes owner; `roles/assign` rejects a 2nd owner with 409) and the **per-app audience split**
(Sniply SPA → `https://sniply-api`; backend accepts both). **Tenant cleanup (re-pulled 2026-06-04):**
stale apps removed; a dedicated **Sniply** API + M2M client added; the **`Plan Selection` Form was
deleted** (the `Update User` flow that wrote user `app_metadata.subscription` is now orphaned). The
**Sync user** post-registration action remains unbound (pending review). See the rows and notes below.

| Capability | Status | # | Verified state (tenant vs code) |
|---|---|---|---|
| PKCE SPA login | ✅ | — | `UpContent SPA` + `Sniply` clients are SPA/auth=none, rotating refresh; both apps use auth0 SDKs. |
| JWT validation (RS256/JWKS, iss/aud/exp) | ✅ | — | `app/security.py`. API `UpContent Services` = `https://upcontent-api`, RS256. |
| M2M Management orchestration | ✅ | — | `UpC Services - MGM API` client grant holds the 12 Mgmt scopes incl. `create:organization_members`. (Deploy CLI uses `Tenant management - DevOps App`.) |
| Create-org → owner flow | ✅ | — | `tasks.create_organization`; tenant has orgs with members + `upcnt_owner`. |
| Invitations / Roles (object-level authz) | ✅ | — | Live ownership check; `upcnt_*` roles exist in tenant. |
| Add-claims action (org context) | ✅ | — | Post-login **"Add Custom Claims"** is deployed **and now bound to post-login** (2026-06-04); stamps `https://upcontent.com/{plan,roles,org_id,org_name}` plus `pending_plan` from the signup `selected-plan` param. |
| DataDog / SIEM log stream | ✅ | #7 | **Already configured** in tenant (PII-hashed). (Earlier analysis wrongly marked this missing.) |
| Attack Protection | ✅ | #15 | **Done (verified 2026-06-04):** brute-force, suspicious-IP, and **breached-password** all **on** (block on pre-login / pre-registration / pre-change-password); bot detection at `medium` (monitoring mode); CAPTCHA (auth challenge) active. |
| Org picker / org-scoped login | ◐ | #8 | `UpContent SPA` set to `organization_usage=allow` (changed 2026-06-04 from `require`) so brand-new users with 0 orgs can authenticate and self-register; app code still doesn't manage multi-org context or show a picker. |
| MFA | ✅ | #6 | **Done (verified 2026-06-04):** factors enabled + enrollable (email, OTP, WebAuthn-platform). No enforcement policy (`guardianPolicies: []`) by design - enforcement is post-MVP per the acceptance criteria. |
| Role → permission model (Table 5) | ◐ | #10 | Only `upcnt_owner` has permissions (`invite:organizationUser`,`update:organization`); admin/editor/manager/reviewer empty. **Owner 1:1 uniqueness now enforced server-side** (2026-06-04): create-org makes the creator the owner; `roles/assign` rejects a 2nd owner with HTTP 409 (`tasks._assert_single_owner`). |
| Self-registration → plan + org | ✅ | — | **Real Auth0 round-trip shipped 2026-06-04:** public pricing page → "Sign up for {plan}" sends `selected-plan` to `/authorize` (`screen_hint=signup`); the bound post-login Action reads `event.request.query['selected-plan']` and stamps a `pending_plan` token claim; on `POST /api/organizations` the backend reads the claim and writes `org.metadata.selected_plan` server-side (A&D Figure 10 - Services creates the org after login). No localStorage. |
| Plan system of record | ◐ | #1 | **App layer consistent** on `org.metadata.selected_plan` (read + write). The `Plan Selection` Form was **deleted** in cleanup; the `Update User` flow (writes user `app_metadata.subscription`) is now **orphaned**. Remaining tenant gap: **Add Custom Claims** reads `org.metadata.plan` (should be `selected_plan`) - see Reconciliation #1. |
| App / audience split + Sniply social | ◐ | #16 | **Per-app audience split wired (2026-06-04):** Sniply SPA requests `https://sniply-api`; backend accepts both `https://upcontent-api` and `https://sniply-api` (`config.auth0_api_audiences`). **Sniply is now a login + profile app** (no org scopes by design) - it reads org/role/plan from the token via `/api/me`, so empty Sniply API scopes are fine. Requires a tenant API with identifier `https://sniply-api` (export still shows `http://sniply`). Social: **only `google-oauth2`** (no Twitter/Facebook/Buffer). |
| Impersonation / RFC 8693 | ✗ | #12 | Not present; pending design (no Login Tickets). |
| Client/port alignment | ✅ | — | **Fixed 2026-06-04**: UpContent(Vue)→:3000 (`UpContent SPA`), Sniply(React)→:3001 (`Sniply`); matched Sniply's trailing-slash callback. |

## Reconciliation notes

1. **Plan system of record → org metadata (decided; app layer done; tenant nearly clean).**
   The **app layer is aligned** on `org.metadata.selected_plan` (backend read + write; the
   public pricing page and create-org flow apply the chosen plan there). The cleanup
   **deleted the `Plan Selection` Form**, so the user-`app_metadata.subscription` writer is
   effectively gone. Two tenant items remain:
   - the deployed **Add Custom Claims** action still reads `org.metadata.plan` (should read `selected_plan`)
   - the **`Update User` flow** is now **orphaned** (writes `app_metadata.subscription` from a
     deleted Form field `choice_aEb8`) - delete it or repoint to `org.metadata.selected_plan`.
   Also standardize the plan catalog ids/prices if the Form is ever reintroduced (the app uses
   `plan1-3` at $9/$29/$99).
2. **Org picker chicken-and-egg (resolved at tenant).** `UpContent SPA` previously required
   an org at login, so a brand-new user with no org could not complete the required picker.
   Resolved 2026-06-04 by setting `organization_usage=allow`, which lets new users
   authenticate and run the app-layer self-registration → plan → create-org flow. Existing
   org members are unaffected.
3. **Self-reg/account flow → real Auth0 round-trip (implemented).**
   Follows the A&D Figure 10 sequence: `selected-plan` on `/authorize` → post-login Action stamps a
   `pending_plan` claim → after login the **SPA calls Services** (`POST /api/organizations`), which
   creates the org, makes the user the owner, and reads the `pending_plan` claim off the token to
   write `org.metadata.selected_plan` server-side. Action status:
   - **Add Custom Claims** (post-login) - **updated + bound to post-login (2026-06-04)** via the
     Management API: reads `event.request.query['selected-plan']` → stamps `pending_plan`, plus the
     org-context claims when present. (Still review the `org.metadata.plan` vs `selected_plan` read in #1.)
   - **Sync user and create account** (post-user-registration, `deployed=false`, unbound) - an
     alternative server-at-registration model expecting a `/auth0/sync` backend and an external
     accounts DB; it calls `api.access.deny` on failure, so **do not bind it** until that backend
     exists. Leave unbound while under review; the app-layer flow covers org creation.
4. **Tenant hygiene.** Stale apps (`Mikes Angular App`, `Mikes Demo App`, `My Angular App`,
   `test`) **removed (2026-06-04)**. Still open: the leftover **`addPlan`** scope on
   `UpContent Services`; empty permissions on the non-owner roles (`upcnt_admin/editor/manager/reviewer`);
   the orphaned `Update User` flow (see #1); Sniply social connections if in scope.
5. **API authorization.** `UpContent Services` uses `subject_type_authorization.user: allow_all`
   and `token_dialect: access_token` — any signed-in user can request the API's scopes, and
   RBAC permissions are not auto-added to the token. This is compatible with the demo's
   object-level (server-side) authorization, but should be a deliberate decision vs. RBAC-gated.
