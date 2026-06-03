# Roadmap

Prioritized backlog to take the demo toward the target end-state. Priority:
P1 (MVP-blocking) · P2 (MVP) · P3 (post-MVP). Feedback # refers to the 2026-05-22
architecture/config review.

| Item | Priority | Feedback # | Acceptance |
|---|---|---|---|
| Org picker / org-scoped login | P1 | #8 | Single org → auto-login into it; multiple → Auth0 org selection prompt; access token carries `org_id`. |
| Owner role 1:1 per-org enforcement | P1 | #10 | App layer rejects assigning a second owner to an org; ownership transfer is explicit. Auth0 can't model this, so enforce server-side. |
| Migration toolkit (3-step) | P1 | #4 / #5 / #14 | Bulk import users with `pbkdf2_sha512` hashes; create orgs; link users to orgs and assign RBAC roles. Idempotent + resumable; source role field = `role on account_user` (privileges deprecated). |
| App / audience split + Sniply social | P2 | #16 | Distinct Sniply API audience if needed; Sniply social connections (Google, Twitter, Facebook, Buffer) enabled on the Sniply app; per-app consent. |
| DataDog / SIEM log stream | P2 | #7 | Tenant log stream to DataDog active; auth events observable. |
| First-party / third-party consent | P2 | #9 | First-party consent disabled; third-party apps prompt for consent. |
| Attack Protection | P2 | #15 | Bot detection, brute-force protection, breached-password detection enabled. |
| MFA | P3 | #6 | Factor(s) defined and enrollable; policy scoped (post-MVP). |
| Impersonation / token exchange | P3 | #12 | Correct RFC 8693 token-exchange design (drop non-existent Login Tickets) or admin impersonation, documented. |

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
