"""Plan selection route (object-level: caller must be member of {org_id})."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from .. import tasks
from ..mgmt_service import ManagementApiError
from ..models import SelectPlanRequest
from ..security import Principal, assert_org_admin, get_principal
from ..validators import ValidationError, require_valid_org_id

log = logging.getLogger("upcontent.routes.plans")
router = APIRouter(prefix="/api/plan", tags=["plans"])


@router.post("/select")
async def select_plan(
    body: SelectPlanRequest,
    principal: Principal = Depends(get_principal),
) -> dict:
    """Select a plan for an org. Caller must be an OWNER/ADMIN of body.org_id.

    Authorized object-level (owner/admin of the target org), not via a token
    scope — so a freshly-assigned org role takes effect with no token refresh.
    The check is inline (not a path-param dependency) because org_id arrives in
    the JSON body for this endpoint.
    """
    try:
        require_valid_org_id(body.org_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Object-level authorization: caller must be an owner/admin of the target org.
    await assert_org_admin(body.org_id, principal.sub)

    try:
        await tasks.select_plan(body.org_id, body.plan)
        return {"status": "ok", "org_id": body.org_id, "plan": body.plan}
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ManagementApiError:
        raise HTTPException(status_code=502, detail="Could not update plan.")
