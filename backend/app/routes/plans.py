"""Plan selection route (object-level: caller must be member of {org_id})."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from .. import tasks
from ..mgmt_service import ManagementApiError
from ..models import SelectPlanRequest
from ..security import Principal, require_org_member, require_scopes
from ..validators import ValidationError, require_valid_org_id

log = logging.getLogger("upcontent.routes.plans")
router = APIRouter(prefix="/api/plan", tags=["plans"])


@router.post("/select")
async def select_plan(
    body: SelectPlanRequest,
    principal: Principal = Depends(require_scopes("update:organizations")),
) -> dict:
    """Select a plan for an org. Caller must be a member of body.org_id.

    Object-level check is performed here (not via path-param dependency)
    because org_id arrives in the JSON body for this endpoint.
    """
    try:
        require_valid_org_id(body.org_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Object-level authorization: caller must be a member of the target org.
    from ..mgmt_service import get_mgmt_service

    orgs = await get_mgmt_service().list_organizations_for_user(principal.sub)
    if not any(o.id == body.org_id for o in orgs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization.",
        )

    try:
        await tasks.select_plan(body.org_id, body.plan)
        return {"status": "ok", "org_id": body.org_id, "plan": body.plan}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not update plan.")
