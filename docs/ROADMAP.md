# Roadmap

Prioritized backlog to take the demo toward the target end-state. Priority:
P1 (MVP-blocking) · P2 (MVP) · P3 (post-MVP). Feedback # refers to the 2026-05-22
architecture/config review.

**Shipped 2026-06-04:** Self-Registration → Selecting a Plan as a **real Auth0 round-trip** -
the pricing page sends `selected-plan` to `/authorize`; the post-login **Add Custom Claims**
Action (updated + **bound to post-login** via the Management API) stamps a `pending_plan` token
claim; `POST /api/organizations` reads the claim and writes `org.metadata.selected_plan`
server-side (no localStorage). `GET /api/plans` made public; tenant `organization_usage=allow`.
Also shipped: **owner 1:1 uniqueness enforced server-side** (#10 - creator becomes owner;
`roles/assign` rejects a 2nd owner with 409) and the **per-app audience split** (Sniply SPA →
`https://sniply-api`; backend accepts both audiences). Follow-on tenant alignment is in the P2 items below.

**Tenant cleanup (re-pulled 2026-06-04):** stale apps removed; dedicated Sniply API
+ M2M client added; `Plan Selection` Form deleted (its `Update User` flow is now
orphaned). The **Sync user** post-registration action remains unbound (pending review).

| Item | Priority | Feedback # | Acceptance |
|---|---|---|---|
| Align plan system of record (tenant) | P2 | #1 | Change **Add Custom Claims** action to read `org.metadata.selected_plan` (not `plan`); **delete the orphaned `Update User` flow** (or repoint it to org metadata); remove the leftover `addPlan` API scope. App layer already consistent on `org.metadata.selected_plan`; the `Plan Selection` Form has been deleted. |
| Finish Sniply audience split | P2 | #16 | **Create a tenant API with identifier `https://sniply-api`** (export still shows `http://sniply`) so Sniply login resolves; **no scopes needed** - Sniply is login + profile only and reads org/role/plan from the token via `/api/me`. Backend already accepts both audiences; Sniply SPA already requests `https://sniply-api` and requests no org scopes. Separately: enable Sniply social connections (Google, Twitter, Facebook, Buffer) + per-app consent. |
| Review post-login / registration actions | P3 | — | **Add Custom Claims** (post-login) is now updated + bound (reads `selected-plan`, stamps `pending_plan`); remaining: reconcile its `org.metadata.plan` vs `selected_plan` read (see plan-SoR item). **Sync user and create account** (post-user-registration) - keep **unbound** until a `/auth0/sync` backend exists (`api.access.deny` would block all registrations if bound). |
| Org picker / org-scoped login | P1 | #8 | Single org → auto-login into it; multiple → Auth0 org selection prompt; access token carries `org_id`. |
| Migration toolkit (3-step) | P1 | #4 / #5 / #14 | Bulk import users with `pbkdf2_sha512` hashes; create orgs; link users to orgs and assign RBAC roles. Idempotent + resumable; source role field = `role on account_user` (privileges deprecated). |
| DataDog / SIEM log stream | P2 | #7 | Tenant log stream to DataDog active; auth events observable. |
| First-party / third-party consent | P2 | #9 | First-party consent disabled; third-party apps prompt for consent. |
| Impersonation / token exchange | P3 | #12 | Correct RFC 8693 token-exchange design (drop non-existent Login Tickets) or admin impersonation, documented. |

**Done at the tenant (verified 2026-06-04):** **Attack Protection (#15)** - brute-force,
suspicious-IP, and breached-password all enabled (block); bot detection `medium`
(monitoring); CAPTCHA active. **MFA (#6)** - email/OTP/WebAuthn-platform factors enabled
and enrollable; enforcement policy intentionally deferred (post-MVP).

## 3-step migration flow

```
[Source: account_user records]
        │
        ▼
(1) Import users  ──────────────►  Auth0 db connection
    • bulk import job                users created with
    • password hashes:               pbkdf2_sha512 preserved
      pbkdf2_sha512                  (no reset needed)
        │
        ▼
(2) Create organizations  ──────►  one Org per account
    • org name + display_name        org-level metadata
    • enable db connection           (e.g. selected plan)
        │
        ▼
(3) Link + assign roles  ───────►  user ↔ org membership
    • add user as org member         + RBAC role per the
    • map source role → Auth0 role   role-to-metadata-then-
      (owner / member)               assign step
```

Note (gap #5): roles must first exist as tenant roles before they can be assigned
to org members; the migration writes the role intent to metadata and then assigns
the matching RBAC role in step 3.
