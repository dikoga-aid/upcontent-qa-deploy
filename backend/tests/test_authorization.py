"""Authorization use-case tests (object-level + owner uniqueness + create-org).

These exercise the design decisions that JWT tests don't cover: per-org
membership/admin checks (verified live against the Management API), the
one-owner-per-org rule, and the create-org flow that makes the creator the
owner and applies a signup-time plan. The Management API is faked so the tests
are hermetic and assert on the authorization logic, not Auth0 wire calls.
"""
import pytest
from fastapi import HTTPException

from app import security, tasks
from app.models import OrgMember, OrgRole, OrgSummary

OWNER = OrgRole(id="rol_owner", name="upcnt_owner", description="")
VIEWER = OrgRole(id="rol_view", name="viewer", description="")

ORG = "org_abc123"
ALICE = "auth0|alice"
BOB = "auth0|bob"


class FakeMgmt:
    """Minimal in-memory stand-in for ManagementService."""

    def __init__(self, memberships=None, member_roles=None, members=None,
                 tenant_roles=None):
        # memberships: {user_id: [OrgSummary, ...]}
        self.memberships = memberships or {}
        # member_roles: {(org_id, user_id): [OrgRole, ...]}
        self.member_roles = member_roles or {}
        # members: {org_id: [OrgMember, ...]}
        self.members = members or {}
        self.tenant_roles = tenant_roles or [OWNER, VIEWER]
        self.calls = []

    async def list_organizations_for_user(self, user_id):
        return self.memberships.get(user_id, [])

    async def get_roles_for_org_member(self, org_id, user_id):
        return self.member_roles.get((org_id, user_id), [])

    async def list_org_members_with_roles(self, org_id):
        return self.members.get(org_id, [])

    async def list_tenant_roles(self):
        return self.tenant_roles

    async def create_organization(self, slug, display_name):
        self.calls.append(("create", slug, display_name))
        return ORG

    async def add_member_to_organization(self, org_id, user_id):
        self.calls.append(("add_member", org_id, user_id))

    async def assign_roles_to_org_member(self, org_id, user_id, role_ids):
        self.calls.append(("assign", org_id, user_id, tuple(role_ids)))

    async def update_org_plan(self, org_id, plan):
        self.calls.append(("plan", org_id, plan))


def _patch(monkeypatch, fake):
    # assert_org_* import get_mgmt_service from .mgmt_service at call time;
    # tasks.* bound it at import. Patch both namespaces.
    monkeypatch.setattr("app.mgmt_service.get_mgmt_service", lambda: fake)
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)


# ── Object-level: membership ───────────────────────────────────────────────

async def test_member_passes(monkeypatch):
    _patch(monkeypatch, FakeMgmt(memberships={ALICE: [OrgSummary(id=ORG)]}))
    await security.assert_org_member(ORG, ALICE)  # no raise


async def test_non_member_403(monkeypatch):
    _patch(monkeypatch, FakeMgmt(memberships={ALICE: []}))
    with pytest.raises(HTTPException) as exc:
        await security.assert_org_member(ORG, ALICE)
    assert exc.value.status_code == 403


# ── Object-level: admin/owner ──────────────────────────────────────────────

async def test_admin_passes(monkeypatch):
    _patch(monkeypatch, FakeMgmt(
        memberships={ALICE: [OrgSummary(id=ORG)]},
        member_roles={(ORG, ALICE): [OWNER]},
    ))
    await security.assert_org_admin(ORG, ALICE)  # no raise


async def test_member_without_admin_role_403(monkeypatch):
    _patch(monkeypatch, FakeMgmt(
        memberships={ALICE: [OrgSummary(id=ORG)]},
        member_roles={(ORG, ALICE): [VIEWER]},
    ))
    with pytest.raises(HTTPException) as exc:
        await security.assert_org_admin(ORG, ALICE)
    assert exc.value.status_code == 403


async def test_non_member_admin_403(monkeypatch):
    _patch(monkeypatch, FakeMgmt(memberships={ALICE: []}))
    with pytest.raises(HTTPException) as exc:
        await security.assert_org_admin(ORG, ALICE)
    assert exc.value.status_code == 403


# ── One-owner-per-org ──────────────────────────────────────────────────────

async def test_second_owner_rejected(monkeypatch):
    # Bob already owns the org; assigning owner to Alice must conflict.
    fake = FakeMgmt(members={ORG: [OrgMember(user_id=BOB, roles=[OWNER])]})
    _patch(monkeypatch, fake)
    with pytest.raises(tasks.OwnerConflictError):
        await tasks.assign_roles(ORG, ALICE, [OWNER.id])


async def test_first_owner_allowed(monkeypatch):
    # No existing owner -> assigning owner to Alice succeeds.
    fake = FakeMgmt(members={ORG: []})
    _patch(monkeypatch, fake)
    await tasks.assign_roles(ORG, ALICE, [OWNER.id])
    assert ("assign", ORG, ALICE, (OWNER.id,)) in fake.calls


async def test_non_owner_role_skips_conflict(monkeypatch):
    # Assigning a non-owner role is never blocked by the owner rule.
    fake = FakeMgmt(members={ORG: [OrgMember(user_id=BOB, roles=[OWNER])]})
    _patch(monkeypatch, fake)
    await tasks.assign_roles(ORG, ALICE, [VIEWER.id])
    assert ("assign", ORG, ALICE, (VIEWER.id,)) in fake.calls


# ── Create-org: creator becomes owner + signup plan applied ────────────────

async def test_create_org_assigns_owner_and_plan(monkeypatch):
    fake = FakeMgmt()
    _patch(monkeypatch, fake)
    org_id, applied = await tasks.create_organization(
        "acme", "Acme Inc.", ALICE, pending_plan="plan2"
    )
    assert org_id == ORG
    assert applied == "plan2"
    assert ("add_member", ORG, ALICE) in fake.calls
    assert ("assign", ORG, ALICE, (OWNER.id,)) in fake.calls
    assert ("plan", ORG, "plan2") in fake.calls


async def test_create_org_without_pending_plan(monkeypatch):
    fake = FakeMgmt()
    _patch(monkeypatch, fake)
    org_id, applied = await tasks.create_organization("acme", "Acme Inc.", ALICE)
    assert org_id == ORG
    assert applied is None
    assert not any(c[0] == "plan" for c in fake.calls)
