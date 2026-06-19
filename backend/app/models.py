"""Plan catalog + request/response models.

Plans: Starter $9 / Professional $29 / Enterprise $99 (ids plan1/plan2/plan3).
"""
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Plan catalog ────────────────────────────────────────────────────────

class Plan(BaseModel):
    id: str
    display_name: str
    description: str
    price: str


PLANS: List[Plan] = [
    Plan(id="plan1", display_name="Starter",
         description="Perfect for individuals getting started", price="$9/mo"),
    Plan(id="plan2", display_name="Professional",
         description="For growing teams and businesses", price="$29/mo"),
    Plan(id="plan3", display_name="Enterprise",
         description="Unlimited scale with dedicated support", price="$99/mo"),
]


# ── Domain DTOs ─────────────────────────────────────────────────────────

class OrgRole(BaseModel):
    id: str
    name: str
    description: str = ""


class OrgSummary(BaseModel):
    id: str
    name: str = ""
    display_name: str = ""
    selected_plan: Optional[str] = None


class OrgMember(BaseModel):
    user_id: str
    name: str = ""
    email: str = ""
    picture: Optional[str] = None
    roles: List[OrgRole] = Field(default_factory=list)


# ── Request bodies ──────────────────────────────────────────────────────

class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., description="Org slug (lowercase, 3-50 chars)")
    display_name: str


class SelectPlanRequest(BaseModel):
    org_id: str
    plan: str


class InviteRequest(BaseModel):
    email: str
    inviter_name: Optional[str] = None
    role_ids: List[str] = Field(default_factory=list)


class RoleChangeRequest(BaseModel):
    user_id: str
    role_ids: List[str]
