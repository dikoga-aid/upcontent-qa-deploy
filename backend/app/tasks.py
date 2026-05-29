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


# Role names that grant org-owner/admin (object-level) rights. The creator is
# auto-assigned the first matching role at org creation.
_ADMIN_ROLE_NAMES = {"org admin", "admin", "organization admin", "owner", "upcnt_owner"}


async def create_organization(slug: str, display_name: str, creator_user_id: str) -> str:
    require_valid_org_slug(slug)
    require_valid_display_name(display_name)
    svc = get_mgmt_service()
    org_id = await svc.create_organization(slug, display_name)
    # Associate the creator so the org appears in *their* list (object-level
    # filter) and they can manage it. Best-effort — never fail the create.
    try:
        await svc.add_member_to_organization(org_id, creator_user_id)
        admin_role = next(
            (r for r in await svc.list_tenant_roles()
             if r.name.strip().lower() in _ADMIN_ROLE_NAMES),
            None,
        )
        if admin_role:
            await svc.assign_roles_to_org_member(org_id, creator_user_id, [admin_role.id])
        else:
            log.warning(
                "Org %s created but no admin-named role exists to grant creator %s; "
                "added as member only (cannot invite/manage roles yet).",
                org_id, creator_user_id,
            )
    except Exception as exc:  # noqa: BLE001
        log.error(
            "Org %s created but could not associate creator %s: %s "
            "(ensure the M2M holds create:organization_members).",
            org_id, creator_user_id, exc,
        )
    return org_id


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
    org_id: str, invitee_email: str, inviter_name: str, client_id: str
) -> None:
    require_valid_org_id(org_id)
    require_valid_email(invitee_email)
    require_valid_display_name(inviter_name)
    await get_mgmt_service().invite_user_to_organization(
        org_id, inviter_name, invitee_email, client_id
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
    await get_mgmt_service().assign_roles_to_org_member(org_id, user_id, role_ids)


async def remove_roles(org_id: str, user_id: str, role_ids: List[str]) -> None:
    require_valid_org_id(org_id)
    require_valid_user_id(user_id)
    for rid in role_ids:
        require_valid_role_id(rid)
    await get_mgmt_service().remove_roles_from_org_member(org_id, user_id, role_ids)
