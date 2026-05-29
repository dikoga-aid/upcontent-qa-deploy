"""Organization routes: list (filtered to caller), create, invite.

Each route enforces a user-token scope (RBAC) AND, for mutations on a specific
org, an object-level membership/admin check.
"""
import logging
import time
from collections import defaultdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from .. import tasks
from ..config import get_settings
from ..mgmt_service import ManagementApiError
from ..models import CreateOrganizationRequest, InviteRequest, OrgSummary
from ..security import (
    Principal,
    require_org_admin,
    require_scopes,
)
from ..validators import ValidationError

log = logging.getLogger("upcontent.routes.organizations")
router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# Lightweight in-memory rate limit for invitations (no infra).
# Maps caller sub -> list of recent invite timestamps.
_INVITE_WINDOW_SECONDS = 60
_INVITE_MAX = 5
_invite_log: dict = defaultdict(list)


def _rate_limit_invites(sub: str) -> None:
    now = time.time()
    recent = [t for t in _invite_log[sub] if now - t < _INVITE_WINDOW_SECONDS]
    if len(recent) >= _INVITE_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invitations. Please wait and try again.",
        )
    recent.append(now)
    _invite_log[sub] = recent


@router.get("", response_model=List[OrgSummary])
async def list_organizations(
    principal: Principal = Depends(require_scopes("read:organizations")),
) -> List[OrgSummary]:
    """Return ONLY the organizations the caller belongs to (object-level filter)."""
    try:
        return await tasks.list_user_organizations(principal.sub)
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Upstream identity service error.")


@router.post("", status_code=201)
async def create_organization(
    body: CreateOrganizationRequest,
    principal: Principal = Depends(require_scopes("create:organizations")),
) -> dict:
    try:
        org_id = await tasks.create_organization(body.name, body.display_name)
        return {"id": org_id, "name": body.name, "display_name": body.display_name}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not create organization.")


@router.post("/{org_id}/invitations", status_code=201)
async def invite(
    body: InviteRequest,
    org_id: str = Depends(require_org_admin),
    principal: Principal = Depends(require_scopes("create:organization_invitations")),
) -> dict:
    _rate_limit_invites(principal.sub)
    inviter = body.inviter_name or principal.claims.get("name") or "An administrator"
    settings = get_settings()
    client_id = settings.auth0_spa_client_id or settings.auth0_mgmt_client_id
    try:
        await tasks.invite_member(org_id, body.email, inviter, client_id)
        return {"status": "sent", "email": body.email}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not send invitation.")
