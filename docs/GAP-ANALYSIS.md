# Gap Analysis

Where the demo stands against the target end-state. Status: ✅ done · ◐ partial ·
✗ not started. "Feedback #" references the 2026-05-22 architecture/config review.
Paraphrased only — see the (confidential) source for full detail.

| Capability | Status | Feedback # | Note |
|---|---|---|---|
| PKCE login (Authorization Code + PKCE, no client secret in browser) | ✅ | — | Both SPAs via Auth0 SDKs. |
| JWT validation (RS256 / JWKS, iss/aud/exp; reject alg:none, HS256, ID tokens) | ✅ | — | `app/security.py`. |
| M2M Management API orchestration (cached client_credentials token) | ✅ | — | `mgmt_token.py` / `mgmt_service.py`. |
| Org-level plan metadata (plan stored on the org, not the user) | ✅ | #1 | `PATCH /organizations/{id}` via Management API. |
| Create-org + owner flow (org → connection → member → owner role) | ✅ | — | `tasks.create_organization`. |
| Invitations (object-level authorized; immediate effect, no refresh) | ✅ | — | `POST /organizations/{org_id}/invitations`. |
| Roles (list members + tenant roles; assign / remove) | ✅ | — | RBAC via Management API. |
| Object-level per-org authorization (live ownership check) | ✅ | — | Not a token scope; takes effect immediately. |
| Owner role 1:1 per-org enforcement (app-layer; Auth0 can't model it) | ◐ | #10 | Owner role assigned at create; uniqueness not yet enforced. |
| Org picker / org-scoped login (single = auto, multiple = picker) | ✗ | #8 | No org selection at login; org chosen in-app. |
| Migration toolkit (user import w/ pbkdf2_sha512 → orgs → user-org + RBAC) | ✗ | #4 / #5 | Not built; sequencing + role-to-metadata gap documented in ROADMAP. |
| App / audience split + Sniply social connections | ◐ | #16 | Two SPA apps now branded correctly; still one shared `upcontent-api` audience; Sniply social (Google/Twitter/Facebook/Buffer) not configured. |
| MFA | ✗ | #6 | Scoped but post-MVP. |
| Impersonation / token exchange (RFC 8693) | ✗ | #12 | Pending design; Login Tickets approach dropped. |
| DataDog / SIEM log stream | ✗ | #7 | MVP-required per review; tenant log stream not configured. |
| First-party / third-party consent policy | ✗ | #9 | Disable first-party, enable third-party — not yet set. |
| Attack Protection (bot detection, brute-force, breached-password) | ✗ | #15 | Tenant setting not enabled. |
