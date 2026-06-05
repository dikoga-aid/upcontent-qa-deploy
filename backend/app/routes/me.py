"""Profile + plan catalog routes (authenticated, no extra scope)."""
from fastapi import APIRouter, Depends

from ..config import CLAIMS_NAMESPACE
from ..models import PLANS, Plan
from ..security import Principal, get_principal

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me")
async def me(principal: Principal = Depends(get_principal)) -> dict:
    """Return the caller's identity, token permissions, and the org context the
    post-login action stamped into the token (org/role/plan), so a SPA can show
    it without any Management API call (used by Sniply, which has no org scopes).
    `pending_plan` is the signup-time `selected-plan`, present until applied."""
    claims = principal.claims
    return {
        "sub": principal.sub,
        "org_id": principal.org_id or claims.get(f"{CLAIMS_NAMESPACE}/org_id"),
        "org_name": claims.get(f"{CLAIMS_NAMESPACE}/org_name"),
        "plan": claims.get(f"{CLAIMS_NAMESPACE}/plan"),
        "pending_plan": claims.get(f"{CLAIMS_NAMESPACE}/pending_plan"),
        "roles": claims.get(f"{CLAIMS_NAMESPACE}/roles") or [],
        "permissions": sorted(principal.scopes),
        # Echo a few standard claims if present (never anything sensitive).
        "email": claims.get("email"),
        "name": claims.get("name"),
    }


@router.get("/plans", response_model=list[Plan])
async def plans() -> list[Plan]:
    # Public: the plan catalog is marketing data, also shown on the logged-out
    # pricing page that drives self-registration (no token required).
    return PLANS
