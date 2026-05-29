"""Profile + plan catalog routes (authenticated, no extra scope)."""
from fastapi import APIRouter, Depends

from ..models import PLANS, Plan
from ..security import Principal, get_principal

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me")
async def me(principal: Principal = Depends(get_principal)) -> dict:
    """Return the caller's identity + the permissions carried by their token."""
    return {
        "sub": principal.sub,
        "org_id": principal.org_id,
        "permissions": sorted(principal.scopes),
        # Echo a few standard claims if present (never anything sensitive).
        "email": principal.claims.get("email"),
        "name": principal.claims.get("name"),
    }


@router.get("/plans", response_model=list[Plan])
async def plans(_: Principal = Depends(get_principal)) -> list[Plan]:
    return PLANS
