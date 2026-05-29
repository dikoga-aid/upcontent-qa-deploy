"""Input validation for user-supplied values before they reach the Auth0
Management API.

Includes Auth0-ID validators (org / user / role): these ids are interpolated
into Management API URLs, so they are format-checked and URL-encoded before use
to block path traversal / SSRF / query-param injection.
"""
import re
from urllib.parse import quote

# RFC 5322 simplified — good enough for a server-side pre-check.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

# Auth0 org slug: lowercase alphanumeric and hyphens, 3-50 chars,
# must start and end with a letter or number.
ORG_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]{1,48}[a-z0-9]$")

# Display name: printable ASCII, 1-100 length.
DISPLAY_NAME_PATTERN = re.compile(r"^[\x20-\x7E]{1,100}$")

# ── Auth0 identifier shapes (path-param injection / SSRF guard) ─────────
ORG_ID_PATTERN = re.compile(r"^org_[A-Za-z0-9]+$")
ROLE_ID_PATTERN = re.compile(r"^rol_[A-Za-z0-9]+$")
# Auth0 user ids look like "<provider>|<id>" e.g. "auth0|abc123",
# "google-oauth2|123", "waad|...". Allow the documented charset only.
USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9._\-]+\|[A-Za-z0-9._\-|@]+$")

VALID_PLAN_IDS = {"plan1", "plan2", "plan3"}


class ValidationError(Exception):
    """Raised when user-supplied input fails validation.

    Routes translate this into an HTTP 422 with a generic, sanitized message.
    """


def _sanitize(value: str) -> str:
    """Strip non-printable chars to prevent log/error injection; cap length."""
    if value is None:
        return ""
    cleaned = re.sub(r"[^\x20-\x7E]", "?", value)
    return cleaned[:40]


# ── User-facing value validators ────────────────────────────────────────

def require_valid_email(email: str) -> str:
    if not email or not email.strip():
        raise ValidationError("Email address is required.")
    if len(email) > 254:
        raise ValidationError("Email address is too long.")
    if not EMAIL_PATTERN.match(email.strip()):
        raise ValidationError(f'"{_sanitize(email)}" is not a valid email address.')
    return email.strip()


def require_valid_org_slug(slug: str) -> str:
    if not slug or not slug.strip():
        raise ValidationError("Organization ID (slug) is required.")
    if not ORG_SLUG_PATTERN.match(slug):
        raise ValidationError(
            "Organization ID must be 3-50 characters, lowercase letters, numbers, "
            "and hyphens only. Must start and end with a letter or number."
        )
    return slug


def require_valid_display_name(name: str) -> str:
    if not name or not name.strip():
        raise ValidationError("Display name is required.")
    if not DISPLAY_NAME_PATTERN.match(name):
        raise ValidationError("Display name must be 1-100 printable characters.")
    return name


def require_valid_plan(plan_id: str) -> str:
    if not plan_id or not plan_id.strip():
        raise ValidationError("A plan selection is required.")
    if plan_id not in VALID_PLAN_IDS:
        raise ValidationError(f'"{_sanitize(plan_id)}" is not a valid plan.')
    return plan_id


# ── Auth0 identifier validators (path-param injection guard) ────────────

def require_valid_org_id(org_id: str) -> str:
    """Validate an Auth0 organization id (``org_...``). Returns it unchanged.

    Rejects path traversal (``../``), URL-encoded payloads, and query injection.
    """
    if not org_id or not ORG_ID_PATTERN.match(org_id):
        raise ValidationError("Invalid organization id.")
    return org_id


def require_valid_role_id(role_id: str) -> str:
    if not role_id or not ROLE_ID_PATTERN.match(role_id):
        raise ValidationError("Invalid role id.")
    return role_id


def require_valid_user_id(user_id: str) -> str:
    if not user_id or len(user_id) > 128 or not USER_ID_PATTERN.match(user_id):
        raise ValidationError("Invalid user id.")
    return user_id


def url_encode(value: str) -> str:
    """URL-encode a path segment before interpolation into a Management URL."""
    return quote(value, safe="")
