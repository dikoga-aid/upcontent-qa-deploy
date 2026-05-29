"""JWT validation + authorization dependencies for the resource server.

Implements the hardened security model from the plan:

1. RS256 ONLY (rejects ``alg:none`` and HS256 — no algorithm confusion).
2. Signature verified against the tenant JWKS (``PyJWKClient``, cached).
3. ``iss``/``aud`` verified; ``exp``/``nbf`` with <=60s leeway. ID tokens
   (aud = SPA client_id) are rejected — the audience MUST be the API.
4. ``require_scopes`` enforces RBAC permissions (checks both the ``scope``
   space-string and the ``permissions`` array Auth0 emits with RBAC).
5. ``require_org_member`` / ``require_org_admin`` enforce object-level
   authorization via the Management API (membership / admin in the target org).
"""
import logging
from typing import Callable, List, Optional, Set

import jwt
from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import Settings, get_settings
from .validators import (
    ValidationError,
    require_valid_org_id,
)

log = logging.getLogger("upcontent.security")

# Name of the tenant role that grants org-admin object-level rights.
ADMIN_ROLE_NAMES = {"org admin", "admin", "organization admin", "owner", "upcnt_owner"}

_bearer = HTTPBearer(auto_error=False)

# One JWKS client per process (caches signing keys internally).
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.jwks_url, cache_keys=True)
    return _jwks_client


class Principal:
    """The authenticated caller, derived from a validated access token."""

    def __init__(self, claims: dict):
        self.claims = claims
        self.sub: str = claims.get("sub", "")
        # Auth0 with RBAC may put grants in `permissions` (array) and/or
        # `scope` (space string). Merge both per the plan gotcha.
        perms: Set[str] = set()
        scope = claims.get("scope")
        if isinstance(scope, str):
            perms.update(scope.split())
        permissions = claims.get("permissions")
        if isinstance(permissions, list):
            perms.update(str(p) for p in permissions)
        self.scopes: Set[str] = perms
        self.org_id: Optional[str] = claims.get("org_id")

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


async def get_principal(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """Validate the Bearer access token and return the Principal.

    Raises 401 for any missing / malformed / invalid token.
    """
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = creds.credentials

    # Reject anything but RS256 up front (defense against alg confusion).
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise _unauthorized("Malformed token.")
    if header.get("alg") != "RS256":
        raise _unauthorized("Unsupported token algorithm.")

    try:
        signing_key = _get_jwks_client(settings).get_signing_key_from_jwt(token)
    except Exception:  # noqa: BLE001 - any JWKS failure is an auth failure
        raise _unauthorized("Could not verify token signature.")

    try:
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.auth0_api_audience,
            issuer=settings.issuer,
            leeway=60,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )
    except jwt.InvalidTokenError:
        # Generic client error; details stay server-side.
        raise _unauthorized("Invalid token.")

    return Principal(claims)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_scopes(*required: str) -> Callable:
    """Dependency factory enforcing that the caller holds all `required` scopes."""

    async def _dep(principal: Principal = Depends(get_principal)) -> Principal:
        missing = [s for s in required if not principal.has_scope(s)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission(s): {', '.join(missing)}",
            )
        return principal

    return _dep


# ── Object-level authorization (membership / admin) ─────────────────────

def _validated_org_id(org_id: str = Path(..., alias="org_id")) -> str:
    try:
        return require_valid_org_id(org_id)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


async def assert_org_member(org_id: str, sub: str) -> None:
    """Raise 403 unless `sub` is a member of `org_id` (live Management API check).

    Usable inline (e.g. when org_id arrives in the request body).
    """
    from .mgmt_service import get_mgmt_service

    orgs = await get_mgmt_service().list_organizations_for_user(sub)
    if not any(o.id == org_id for o in orgs):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization.",
        )


async def assert_org_admin(org_id: str, sub: str) -> None:
    """Raise 403 unless `sub` is an owner/admin of `org_id` (member + admin role)."""
    from .mgmt_service import get_mgmt_service

    await assert_org_member(org_id, sub)
    roles = await get_mgmt_service().get_roles_for_org_member(org_id, sub)
    if not ({r.name.strip().lower() for r in roles} & ADMIN_ROLE_NAMES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner or admin role required for this organization.",
        )


async def require_org_member(
    org_id: str = Depends(_validated_org_id),
    principal: Principal = Depends(get_principal),
) -> str:
    """Path-param dependency: caller must be a member of `org_id`. Returns it."""
    await assert_org_member(org_id, principal.sub)
    return org_id


async def require_org_admin(
    org_id: str = Depends(_validated_org_id),
    principal: Principal = Depends(get_principal),
) -> str:
    """Path-param dependency: caller must be an owner/admin of `org_id`. Returns it."""
    await assert_org_admin(org_id, principal.sub)
    return org_id
