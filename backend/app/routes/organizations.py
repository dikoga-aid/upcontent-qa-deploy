"""Organization routes: list (your orgs), create, invite.

list/create require a baseline token scope (read/create:organization). invite is
authorized object-level — you must be an owner/admin of the target org — so it
needs no token scope and works the moment the owner role is granted (no refresh).
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .. import tasks
from ..config import CLAIMS_NAMESPACE, get_settings
from ..mgmt_service import ManagementApiError
from ..models import CreateOrganizationRequest, InviteRequest, OrgSummary
from ..security import Principal, get_principal, require_org_admin, require_scopes
from ..validators import ValidationError

log = logging.getLogger("upcontent.routes.organizations")
router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=List[OrgSummary])
async def list_organizations(
    principal: Principal = Depends(require_scopes("read:organization")),
) -> List[OrgSummary]:
    """Return ONLY the organizations the caller belongs to (object-level filter)."""
    try:
        return await tasks.list_user_organizations(principal.sub)
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Upstream identity service error.")


@router.post("", status_code=201)
async def create_organization(
    body: CreateOrganizationRequest,
    principal: Principal = Depends(require_scopes("create:organization")),
) -> dict:
    # Self-registration: a plan chosen at signup arrives as the `pending_plan`
    # token claim (stamped by the post-login Action from the `selected-plan`
    # Authorize param). Apply it to the new org server-side.
    pending_plan = principal.claims.get(f"{CLAIMS_NAMESPACE}/pending_plan")
    try:
        org_id, applied_plan = await tasks.create_organization(
            body.name, body.display_name, principal.sub, pending_plan=pending_plan
        )
        return {
            "id": org_id,
            "name": body.name,
            "display_name": body.display_name,
            "selected_plan": applied_plan,
        }
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not create organization.")


@router.post("/{org_id}/invitations", status_code=201)
async def invite(
    body: InviteRequest,
    # No token scope required: invite is authorized purely by being an owner/admin
    # of THIS org, verified live server-side (require_org_admin → Management API).
    # The owner role is assigned at org creation, so it takes effect immediately —
    # no token refresh or re-login. The Management scope used to send the invite
    # (create:organization_invitations) is held by the backend M2M only.
    org_id: str = Depends(require_org_admin),
    principal: Principal = Depends(get_principal),
) -> dict:
    # NOTE: in production, throttle Management API calls (e.g. invitations) to
    # respect Auth0 rate limits. Omitted here to keep the demo focused on auth.
    inviter = (
        body.inviter_name
        or principal.claims.get("name")
        or principal.claims.get("email")  # fallback when profile name is null
        or "An administrator"
    )
    # auth0_spa_client_id is required at startup (no M2M fallback — that would
    # silently embed the wrong client_id in the invite link and break PKCE).
    settings = get_settings()
    client_id = settings.auth0_spa_client_id
    try:
        await tasks.invite_member(org_id, body.email, inviter, client_id, role_ids=body.role_ids)
        return {"status": "sent", "email": body.email}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not send invitation.")
