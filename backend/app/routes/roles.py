"""Org member role routes: view members (member), assign/remove (admin)."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from .. import tasks
from ..mgmt_service import ManagementApiError
from ..models import RoleChangeRequest
from ..security import (
    Principal,
    require_org_admin,
    require_org_member,
    require_scopes,
)
from ..validators import ValidationError

log = logging.getLogger("upcontent.routes.roles")
router = APIRouter(prefix="/api/organizations", tags=["roles"])


@router.get("/{org_id}/roles")
async def list_roles(
    org_id: str = Depends(require_org_member),
    _: Principal = Depends(require_scopes("read:organization")),
) -> dict:
    """Members of the org (with roles) + the tenant role catalog."""
    try:
        members = await tasks.list_members_with_roles(org_id)
        tenant_roles = await tasks.list_tenant_roles()
        return {
            "org_id": org_id,
            "members": [m.model_dump() for m in members],
            "tenant_roles": [r.model_dump() for r in tenant_roles],
        }
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not load org members.")


@router.post("/{org_id}/roles/assign")
async def assign_roles(
    body: RoleChangeRequest,
    # Authorized object-level (owner/admin of this org), no token scope.
    org_id: str = Depends(require_org_admin),
) -> dict:
    try:
        await tasks.assign_roles(org_id, body.user_id, body.role_ids)
        return {"status": "assigned", "count": len(body.role_ids)}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not assign roles.")


@router.post("/{org_id}/roles/remove")
async def remove_roles(
    body: RoleChangeRequest,
    # Authorized object-level (owner/admin of this org), no token scope.
    org_id: str = Depends(require_org_admin),
) -> dict:
    try:
        await tasks.remove_roles(org_id, body.user_id, body.role_ids)
        return {"status": "removed", "count": len(body.role_ids)}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not remove roles.")
