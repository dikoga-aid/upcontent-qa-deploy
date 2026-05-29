"""Input + Auth0-id validation tests.

The Auth0-id guards are the security-critical ones: org/user/role ids are
interpolated into Management API URLs, so they must reject path/query injection.
"""
import pytest

from app.validators import (
    ValidationError,
    require_valid_display_name,
    require_valid_email,
    require_valid_org_id,
    require_valid_org_slug,
    require_valid_plan,
    require_valid_role_id,
    require_valid_user_id,
)


# ── User input validated before it reaches the Management API ──────────────

@pytest.mark.parametrize(
    "fn,value,ok",
    [
        (require_valid_email, "user@example.com", True),
        (require_valid_email, "not-an-email", False),
        (require_valid_org_slug, "my-org", True),
        (require_valid_org_slug, "Bad_Slug", False),
        (require_valid_display_name, "Acme Inc.", True),
        (require_valid_display_name, "emoji \U0001F600", False),
        (require_valid_plan, "plan2", True),
        (require_valid_plan, "free", False),
    ],
)
def test_input_validation(fn, value, ok):
    if ok:
        assert fn(value) == value
    else:
        with pytest.raises(ValidationError):
            fn(value)


# ── Auth0 id injection guards (org/user/role → Management API URLs) ────────

@pytest.mark.parametrize("org_id", ["org_abc123", "org_ABC0099"])
def test_valid_org_ids(org_id):
    assert require_valid_org_id(org_id) == org_id


@pytest.mark.parametrize(
    "org_id",
    [
        "",
        "org_",                 # no id chars
        "org_%2e%2e",           # encoded traversal
        "../../etc/passwd",
        "org_abc/roles",        # path injection
        "org_abc?x=1",          # query injection
        "rol_abc",              # wrong prefix
    ],
)
def test_org_id_rejects_injection(org_id):
    with pytest.raises(ValidationError):
        require_valid_org_id(org_id)


@pytest.mark.parametrize("role_id", ["rol_abc123", "rol_XYZ0"])
def test_valid_role_ids(role_id):
    assert require_valid_role_id(role_id) == role_id


@pytest.mark.parametrize("role_id", ["", "role_abc", "rol_", "rol_abc/x", "org_abc"])
def test_role_id_rejects_injection(role_id):
    with pytest.raises(ValidationError):
        require_valid_role_id(role_id)


@pytest.mark.parametrize(
    "user_id", ["auth0|abc123", "google-oauth2|107", "waad|tenant|user"]
)
def test_valid_user_ids(user_id):
    assert require_valid_user_id(user_id) == user_id


@pytest.mark.parametrize(
    "user_id", ["", "no-pipe", "auth0|abc/../x", "auth0|abc def", "x" * 200 + "|y"]
)
def test_user_id_rejects_injection(user_id):
    with pytest.raises(ValidationError):
        require_valid_user_id(user_id)
