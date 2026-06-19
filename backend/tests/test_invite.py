"""Invite-flow unit tests: role forwarding, config hardening, inviter-name fallback.

Maps to VOL-1 acceptance criteria:
- AC 2: role_ids forwarded to the Management API invitation body (Bug 2 fix).
- AC 6: AUTH0_SPA_CLIENT_ID required; absent -> startup fails.
- Inviter-name spec: email fallback when the 'name' claim is absent.
"""
import pytest
from typing import List, Optional

from app import tasks
from app.config import get_settings
from app.models import OrgRole
from app.validators import ValidationError

ORG = "org_abc123"
INVITEE = "invited@example.com"
SPA_CLIENT = "test-spa-client-id"


class FakeInviteMgmt:
    def __init__(self):
        self.calls: list = []

    async def invite_user_to_organization(
        self,
        org_id: str,
        inviter_name: str,
        invitee_email: str,
        client_id: str,
        role_ids: Optional[List[str]] = None,
    ) -> None:
        self.calls.append(
            dict(
                org_id=org_id,
                invitee_email=invitee_email,
                inviter_name=inviter_name,
                client_id=client_id,
                role_ids=role_ids,
            )
        )


# ── AC 2: role forwarding (Bug 2) ─────────────────────────────────────────

async def test_invite_forwards_role_ids(monkeypatch):
    """role_ids are forwarded verbatim to the Management API invitation body."""
    fake = FakeInviteMgmt()
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)
    await tasks.invite_member(ORG, INVITEE, "Alice", SPA_CLIENT, role_ids=["rol_AbCdEf"])
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["role_ids"] == ["rol_AbCdEf"]
    assert call["invitee_email"] == INVITEE
    assert call["client_id"] == SPA_CLIENT


async def test_invite_multiple_role_ids(monkeypatch):
    """Multiple role_ids are all forwarded."""
    fake = FakeInviteMgmt()
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)
    await tasks.invite_member(
        ORG, INVITEE, "Alice", SPA_CLIENT, role_ids=["rol_AbCdEf", "rol_XyZ123"]
    )
    assert fake.calls[0]["role_ids"] == ["rol_AbCdEf", "rol_XyZ123"]


async def test_invite_empty_role_ids(monkeypatch):
    """Inviting without roles still reaches the Management API with an empty list."""
    fake = FakeInviteMgmt()
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)
    await tasks.invite_member(ORG, INVITEE, "Alice", SPA_CLIENT, role_ids=[])
    assert fake.calls[0]["role_ids"] == []


async def test_invite_no_role_ids_defaults_to_empty(monkeypatch):
    """Omitting role_ids defaults to an empty list (backwards-compatible)."""
    fake = FakeInviteMgmt()
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)
    await tasks.invite_member(ORG, INVITEE, "Alice", SPA_CLIENT)
    assert fake.calls[0]["role_ids"] == []


async def test_invite_invalid_role_id_rejected(monkeypatch):
    """Role IDs not matching rol_[A-Za-z0-9]+ are rejected before the API call."""
    fake = FakeInviteMgmt()
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)
    with pytest.raises(ValidationError):
        await tasks.invite_member(ORG, INVITEE, "Alice", SPA_CLIENT, role_ids=["not-valid-id"])
    assert fake.calls == []


async def test_invite_role_id_path_traversal_rejected(monkeypatch):
    """Path-traversal payloads in role_ids are rejected."""
    fake = FakeInviteMgmt()
    monkeypatch.setattr(tasks, "get_mgmt_service", lambda: fake)
    with pytest.raises(ValidationError):
        await tasks.invite_member(
            ORG, INVITEE, "Alice", SPA_CLIENT, role_ids=["../evil"]
        )
    assert fake.calls == []


# ── AC 6: AUTH0_SPA_CLIENT_ID required at startup ────────────────────────

def test_spa_client_id_required(monkeypatch):
    """Settings raises when AUTH0_SPA_CLIENT_ID is absent."""
    from pydantic import ValidationError as PydanticValidationError
    from app.config import Settings

    monkeypatch.delenv("AUTH0_SPA_CLIENT_ID", raising=False)
    monkeypatch.setenv("AUTH0_DOMAIN", "test.us.auth0.com")
    get_settings.cache_clear()

    with pytest.raises(PydanticValidationError):
        Settings()

    get_settings.cache_clear()


def test_spa_client_id_accepted_when_set(monkeypatch):
    """Settings constructs successfully when AUTH0_SPA_CLIENT_ID is present."""
    from app.config import Settings

    monkeypatch.setenv("AUTH0_DOMAIN", "test.us.auth0.com")
    monkeypatch.setenv("AUTH0_SPA_CLIENT_ID", "correct-spa-client")
    get_settings.cache_clear()

    s = Settings()
    assert s.auth0_spa_client_id == "correct-spa-client"
    get_settings.cache_clear()


# ── Inviter-name fallback (spec: email when profile name is null) ─────────

async def test_inviter_name_email_fallback(monkeypatch):
    """Route uses the 'email' claim when 'name' is absent."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routes.organizations import router as org_router
    from app.security import get_principal, require_org_admin, Principal

    captured: list = []

    async def fake_invite_member(
        org_id, invitee_email, inviter_name, client_id, role_ids=None
    ):
        captured.append(inviter_name)

    monkeypatch.setattr(tasks, "invite_member", fake_invite_member)
    monkeypatch.setenv("AUTH0_DOMAIN", "test.us.auth0.com")
    monkeypatch.setenv("AUTH0_SPA_CLIENT_ID", SPA_CLIENT)
    get_settings.cache_clear()

    principal_email_only = Principal({"sub": "auth0|alice", "email": "alice@example.com"})

    app = FastAPI()
    app.include_router(org_router)
    app.dependency_overrides[require_org_admin] = lambda: ORG
    app.dependency_overrides[get_principal] = lambda: principal_email_only

    client = TestClient(app)
    r = client.post(
        f"/api/organizations/{ORG}/invitations",
        json={"email": INVITEE, "role_ids": []},
        headers={"Authorization": "Bearer fake"},
    )
    assert r.status_code == 201
    assert captured[0] == "alice@example.com"
    get_settings.cache_clear()


async def test_inviter_name_prefers_name_claim(monkeypatch):
    """Route prefers 'name' claim over 'email' when both are present."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routes.organizations import router as org_router
    from app.security import get_principal, require_org_admin, Principal

    captured: list = []

    async def fake_invite_member(
        org_id, invitee_email, inviter_name, client_id, role_ids=None
    ):
        captured.append(inviter_name)

    monkeypatch.setattr(tasks, "invite_member", fake_invite_member)
    monkeypatch.setenv("AUTH0_DOMAIN", "test.us.auth0.com")
    monkeypatch.setenv("AUTH0_SPA_CLIENT_ID", SPA_CLIENT)
    get_settings.cache_clear()

    principal_with_name = Principal(
        {"sub": "auth0|alice", "name": "Alice Smith", "email": "alice@example.com"}
    )

    app = FastAPI()
    app.include_router(org_router)
    app.dependency_overrides[require_org_admin] = lambda: ORG
    app.dependency_overrides[get_principal] = lambda: principal_with_name

    client = TestClient(app)
    r = client.post(
        f"/api/organizations/{ORG}/invitations",
        json={"email": INVITEE, "role_ids": []},
        headers={"Authorization": "Bearer fake"},
    )
    assert r.status_code == 201
    assert captured[0] == "Alice Smith"
    get_settings.cache_clear()
