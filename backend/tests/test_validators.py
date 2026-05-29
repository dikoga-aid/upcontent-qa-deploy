"""Validator tests — ports of InputValidatorTest plus Auth0-ID guards."""
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


# ── Email ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("email", ["a@b.co", "user.name@example.com", "x@y.io"])
def test_valid_emails(email):
    assert require_valid_email(email) == email


@pytest.mark.parametrize("email", ["", "no-at-sign", "a@b", "a@@b.com", "a@b.c"])
def test_invalid_emails(email):
    with pytest.raises(ValidationError):
        require_valid_email(email)


def test_email_too_long():
    with pytest.raises(ValidationError):
        require_valid_email("a" * 250 + "@example.com")


# ── Org slug ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("slug", ["abc", "my-org", "org123", "a1b2c3"])
def test_valid_org_slugs(slug):
    assert require_valid_org_slug(slug) == slug


@pytest.mark.parametrize("slug", ["", "ab", "-bad", "bad-", "UPPER", "a b", "a", "x" * 60])
def test_invalid_org_slugs(slug):
    with pytest.raises(ValidationError):
        require_valid_org_slug(slug)


# ── Display name ──────────────────────────────────────────────────────────

def test_valid_display_name():
    assert require_valid_display_name("Acme Inc.") == "Acme Inc."


@pytest.mark.parametrize("name", ["", "x" * 101, "bad\x00name", "emoji\U0001F600"])
def test_invalid_display_name(name):
    with pytest.raises(ValidationError):
        require_valid_display_name(name)


# ── Plan ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("plan", ["plan1", "plan2", "plan3"])
def test_valid_plans(plan):
    assert require_valid_plan(plan) == plan


@pytest.mark.parametrize("plan", ["", "plan4", "free", "PLAN1"])
def test_invalid_plans(plan):
    with pytest.raises(ValidationError):
        require_valid_plan(plan)


# ── Auth0 ID guards (path-param injection) ────────────────────────────────

@pytest.mark.parametrize("org_id", ["org_abc123", "org_ABC0099"])
def test_valid_org_ids(org_id):
    assert require_valid_org_id(org_id) == org_id


@pytest.mark.parametrize(
    "org_id",
    [
        "",
        "org_",                 # no id chars
        "org_..%2f",            # traversal
        "org_%2e%2e",           # encoded traversal
        "../../etc/passwd",
        "org_abc/roles",        # path injection
        "org_abc?x=1",          # query injection
        "rol_abc",              # wrong prefix
    ],
)
def test_invalid_org_ids(org_id):
    with pytest.raises(ValidationError):
        require_valid_org_id(org_id)


@pytest.mark.parametrize("role_id", ["rol_abc123", "rol_XYZ0"])
def test_valid_role_ids(role_id):
    assert require_valid_role_id(role_id) == role_id


@pytest.mark.parametrize("role_id", ["", "role_abc", "rol_", "rol_abc/x", "org_abc"])
def test_invalid_role_ids(role_id):
    with pytest.raises(ValidationError):
        require_valid_role_id(role_id)


@pytest.mark.parametrize(
    "user_id",
    ["auth0|abc123", "google-oauth2|107", "waad|tenant|user", "email|user@x.com"],
)
def test_valid_user_ids(user_id):
    assert require_valid_user_id(user_id) == user_id


@pytest.mark.parametrize(
    "user_id",
    ["", "no-pipe", "auth0|abc/../x", "auth0|abc def", "x" * 200 + "|y"],
)
def test_invalid_user_ids(user_id):
    with pytest.raises(ValidationError):
        require_valid_user_id(user_id)
