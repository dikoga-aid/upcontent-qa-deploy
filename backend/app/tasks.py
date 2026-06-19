"""Management API flows: thin orchestration that validates inputs and composes
Management API calls into the app's operations (e.g. "create org" = create org +
enable connection + add the creator as owner), keeping the routers thin.

REQUIRED_MGMT_SCOPES documents the Management API scopes the server-side M2M
client must hold (least privilege). User-token scopes are enforced separately,
per route, in ``security.require_scopes``.
"""
import logging
from typing import List, Optional

from .mgmt_service import get_mgmt_service
from .models import OrgMember, OrgRole, OrgSummary
from .validators import (
    require_valid_display_name,
    require_valid_email,
    require_valid_org_id,
    require_valid_org_slug,
    require_valid_plan,
    require_valid_role_id,
    require_valid_user_id,
)

log = logging.getLogger("upcontent.tasks")

# Management API scopes the M2M client must hold (least privilege).
REQUIRED_MGMT_SCOPES = [
    "read:organizations",
    "create:organizations",
    "update:organizations",
    "create:organization_invitations",
    "create:organization_members",
    "read:organization_members",
    "read:organization_member_roles",
    "create:organization_member_roles",
    "delete:organization_member_roles",
    "read:roles",
    "read:connections",
    "create:organization_connections",
]


# Role names that grant org-owner/admin (object-level) rights.
_ADMIN_ROLE_NAMES = {"org admin", "admin", "organization admin", "owner", "upcnt_owner"}
# The single-owner role. An org has at most one member holding it (A&D: owner is
# 1:1 per org). Admins may be many; only the owner is unique.
OWNER_ROLE_NAMES = {"owner", "upcnt_owner"}


class OwnerConflictError(Exception):
    """Raised when assigning an owner role would create a second org owner."""


async def create_organization(
    slug: str,
    display_name: str,
    creator_user_id: str,
    pending_plan: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """Create an org, make the creator its owner, and (if a signup `pending_plan`
    was carried in the token) apply it. Returns (org_id, applied_plan_or_None)."""
    require_valid_org_slug(slug)
    require_valid_display_name(display_name)
    svc = get_mgmt_service()
    org_id = await svc.create_organization(slug, display_name)
    # Associate the creator so the org appears in *their* list (object-level
    # filter) and they can manage it. Best-effort — never fail the create.
    try:
        await svc.add_member_to_organization(org_id, creator_user_id)
        roles = await svc.list_tenant_roles()
        # Make the creator the org owner (prefer an owner-named role; fall back
        # to any admin-named role so they can at least manage the org).
        first_owner = next(
            (r for r in roles if r.name.strip().lower() in OWNER_ROLE_NAMES), None
        )
        grant_role = first_owner or next(
            (r for r in roles if r.name.strip().lower() in _ADMIN_ROLE_NAMES), None
        )
        if grant_role:
            await svc.assign_roles_to_org_member(org_id, creator_user_id, [grant_role.id])
        else:
            log.warning(
                "Org %s created but no owner/admin-named role exists to grant creator %s; "
                "added as member only (cannot invite/manage roles yet).",
                org_id, creator_user_id,
            )
    except Exception as exc:  # noqa: BLE001
        log.error(
            "Org %s created but could not associate creator %s: %s "
            "(ensure the M2M holds create:organization_members).",
            org_id, creator_user_id, exc,
        )
    # Apply the signup-time plan (from the `pending_plan` token claim). Best-effort:
    # the org exists regardless; the plan can still be set from the Plans tab.
    applied_plan: Optional[str] = None
    if pending_plan:
        try:
            require_valid_plan(pending_plan)
            await svc.update_org_plan(org_id, pending_plan)
            applied_plan = pending_plan
        except Exception as exc:  # noqa: BLE001
            log.warning("Org %s created but could not apply pending plan %r: %s",
                        org_id, pending_plan, exc)
    return org_id, applied_plan


async def list_user_organizations(user_id: str) -> List[OrgSummary]:
    """List the orgs the caller belongs to, enriched with each org's plan."""
    svc = get_mgmt_service()
    orgs = await svc.list_organizations_for_user(user_id)
    for org in orgs:
        if org.selected_plan is None:
            org.selected_plan = await svc.get_org_plan(org.id)
    return orgs


async def select_plan(org_id: str, plan: str) -> None:
    require_valid_org_id(org_id)
    require_valid_plan(plan)
    await get_mgmt_service().update_org_plan(org_id, plan)


async def invite_member(
    org_id: str,
    invitee_email: str,
    inviter_name: str,
    client_id: str,
    role_ids: Optional[List[str]] = None,
) -> None:
    require_valid_org_id(org_id)
    require_valid_email(invitee_email)
    require_valid_display_name(inviter_name)
    for rid in (role_ids or []):
        require_valid_role_id(rid)
    await get_mgmt_service().invite_user_to_organization(
        org_id, inviter_name, invitee_email, client_id, role_ids=role_ids or []
    )


async def list_tenant_roles() -> List[OrgRole]:
    return await get_mgmt_service().list_tenant_roles()


async def list_members_with_roles(org_id: str) -> List[OrgMember]:
    require_valid_org_id(org_id)
    return await get_mgmt_service().list_org_members_with_roles(org_id)


async def assign_roles(org_id: str, user_id: str, role_ids: List[str]) -> None:
    require_valid_org_id(org_id)
    require_valid_user_id(user_id)
    for rid in role_ids:
        require_valid_role_id(rid)
    svc = get_mgmt_service()
    await _assert_single_owner(svc, org_id, user_id, role_ids)
    await svc.assign_roles_to_org_member(org_id, user_id, role_ids)


async def _assert_single_owner(svc, org_id: str, user_id: str, role_ids: List[str]) -> None:
    """Enforce one owner per org (A&D). Auth0 has no native constraint for this,
    so the app checks live against the Management API: if the assignment includes
    an owner role and a *different* member already holds one, reject it."""
    tenant_roles = await svc.list_tenant_roles()
    owner_role_ids = {
        r.id for r in tenant_roles if r.name.strip().lower() in OWNER_ROLE_NAMES
    }
    if not owner_role_ids or not (set(role_ids) & owner_role_ids):
        return  # not assigning an owner role; nothing to enforce
    for member in await svc.list_org_members_with_roles(org_id):
        if member.user_id == user_id:
            continue
        if {r.id for r in member.roles} & owner_role_ids:
            raise OwnerConflictError(
                "This organization already has an owner. Remove the current "
                "owner or transfer ownership before assigning a new one."
            )


async def remove_roles(org_id: str, user_id: str, role_ids: List[str]) -> None:
    require_valid_org_id(org_id)
    require_valid_user_id(user_id)
    for rid in role_ids:
        require_valid_role_id(rid)
    await get_mgmt_service().remove_roles_from_org_member(org_id, user_id, role_ids)
