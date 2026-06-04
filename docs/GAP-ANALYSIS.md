# Gap Analysis (verified)

Verified **2026-06-04** against the live tenant export (`a0deploy export`), the repo
code, and the A&D v2. Status: ✅ done · ◐ partial · ✗ not started · ⚠️ inconsistent.
"#" references the 2026-05-22 review. Paraphrased — see the (confidential) A&D for detail.

| Capability | Status | # | Verified state (tenant vs code) |
|---|---|---|---|
| PKCE SPA login | ✅ | — | `UpContent SPA` + `Sniply` clients are SPA/auth=none, rotating refresh; both apps use auth0 SDKs. |
| JWT validation (RS256/JWKS, iss/aud/exp) | ✅ | — | `app/security.py`. API `UpContent Services` = `https://upcontent-api`, RS256. |
| M2M Management orchestration | ✅ | — | `MGM API` client grant holds the 12 Mgmt scopes incl. `create:organization_members`. |
| Create-org → owner flow | ✅ | — | `tasks.create_organization`; tenant has orgs with members + `upcnt_owner`. |
| Invitations / Roles (object-level authz) | ✅ | — | Live ownership check; `upcnt_*` roles exist in tenant. |
| Add-claims action (org context) | ✅ | — | Deployed post-login **"Add Custom Claims"** stamps `https://upcontent.com/{plan,roles,org_id,org_name}`. |
| DataDog / SIEM log stream | ✅ | #7 | **Already configured** in tenant (PII-hashed). (Earlier analysis wrongly marked this missing.) |
| Attack Protection | ◐ | #15 | brute-force + suspicious-IP **on**; bot-detection **monitoring-only**; breached-password **off**. |
| Org picker / org-scoped login | ◐ | #8 | **Configured** on `UpContent SPA` (`organization_usage=require`, `post_login_prompt`); app code doesn't manage org context, and new users (0 orgs) can't pass the required picker. |
| MFA | ◐ | #6 | Factors **on** (OTP/email/WebAuthn-platform), **no enforcement policy** — matches post-MVP. |
| Role → permission model (Table 5) | ◐ | #10 | Only `upcnt_owner` has permissions (`invite:organizationUser`,`update:organization`); admin/editor/manager/reviewer empty. Owner 1:1 uniqueness not enforced. |
| Self-registration → account/org | ◐ | — | Post-registration **"Sync user and create account"** action exists but **not deployed**; expects backend `/auth0/sync` (not in the demo). |
| Plan system of record | ⚠️ | #1 | **Split 3 ways** — see Reconciliation #1. Decision: **org metadata** is canonical. |
| App / audience split + Sniply social | ◐ | #16 | Separate `Sniply` client exists; **only `google-oauth2`** social connection (no Twitter/Facebook/Buffer); single shared `upcontent-api` audience. |
| Impersonation / RFC 8693 | ✗ | #12 | Not present; pending design (no Login Tickets). |
| Client/port alignment | ✅ | — | **Fixed 2026-06-04**: UpContent(Vue)→:3000 (`UpContent SPA`), Sniply(React)→:3001 (`Sniply`); matched Sniply's trailing-slash callback. |

## Reconciliation notes

1. **Plan system of record → org metadata (decided).** Today the value lives in three
   places that disagree:
   - demo backend writes/reads `org.metadata.selected_plan`
   - the deployed **Add Custom Claims** action reads `org.metadata.plan`
   - the **Plan Selection** Form → **Update User** Flow writes **user `app_metadata.subscription`**
   Align all to **`org.metadata.selected_plan`**: repoint the Form/Flow to write org metadata
   (not user), change the claims action to read `selected_plan`, and standardize the plan
   catalog (the Form shows `Plan1/2/3 + Free Trial` at $95/$265/Request; the demo uses
   `plan1-3` at $9/$29/$99 — pick one set of ids + prices).
2. **Org picker chicken-and-egg.** `UpContent SPA` requires an org at login. A brand-new
   user has no org and cannot complete the required picker — resolved by deploying the
   self-registration action (creates an org on signup). Existing org members are unaffected.
3. **Self-reg/account flow.** Deploy "Sync user and create account" and add a backend
   `/auth0/sync` endpoint, or drop the action if accounts are created another way.
4. **Tenant hygiene.** Remove stale apps (`Mikes Angular App`, `Mikes Demo App`,
   `My Angular App`, `test`) and the leftover `addPlan` API scope; populate permissions on
   the non-owner roles; add Sniply social connections if in scope.
5. **API authorization.** `UpContent Services` uses `subject_type_authorization.user: allow_all`
   and `token_dialect: access_token` — any signed-in user can request the API's scopes, and
   RBAC permissions are not auto-added to the token. This is compatible with the demo's
   object-level (server-side) authorization, but should be a deliberate decision vs. RBAC-gated.
