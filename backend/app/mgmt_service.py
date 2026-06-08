"""Auth0 Management API client (built on the official ``auth0-python`` SDK).

The SDK is synchronous, so every call runs in a worker thread via
``asyncio.to_thread`` to keep the FastAPI event loop unblocked. A fresh
``Auth0`` client is created per call from the cached M2M token (see
``mgmt_token``). JSON bodies are plain dicts and user-supplied ids are passed
as SDK arguments (the SDK URL-encodes path segments), so no manual encoding or
string-built JSON is needed.
"""
import asyncio
import logging
from typing import Any, Callable, List, Optional

from auth0.exceptions import Auth0Error
from auth0.management import Auth0

from .config import Settings, get_settings
from .mgmt_token import ManagementTokenProvider, get_token_provider
from .models import OrgMember, OrgRole, OrgSummary

log = logging.getLogger("upcontent.mgmt_service")


class ManagementService:
    def __init__(self, settings: Settings, token_provider: ManagementTokenProvider):
        self._s = settings
        self._tokens = token_provider

    async def _client(self) -> Auth0:
        """A Management API client bound to a fresh (cached) M2M token."""
        token = await self._tokens.get_token()
        return Auth0(self._s.auth0_domain, token)

    async def _call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a synchronous SDK method in a worker thread."""
        return await asyncio.to_thread(fn, *args, **kwargs)

    # ── Organization plan (metadata) ──────────────────────────────────

    async def update_org_plan(self, org_id: str, plan: str) -> None:
        """Set org metadata.selected_plan. Requires update:organizations."""
        mgmt = await self._client()
        try:
            await self._call(
                mgmt.organizations.update_organization,
                org_id,
                {"metadata": {"selected_plan": plan}},
            )
        except Auth0Error as exc:
            raise _mgmt_error("update org plan", exc)
        log.info("Updated plan for org %s to '%s'", org_id, plan)

    async def get_org_plan(self, org_id: str) -> Optional[str]:
        """Read org metadata.selected_plan. Requires read:organizations."""
        mgmt = await self._client()
        try:
            org = await self._call(mgmt.organizations.get_organization, org_id)
        except Auth0Error as exc:
            log.warning("Could not fetch org [%s] for plan lookup: %s", org_id, exc.status_code)
            return None
        return ((org or {}).get("metadata") or {}).get("selected_plan")

    # ── Connections ───────────────────────────────────────────────────

    async def get_default_database_connection_id(self) -> Optional[str]:
        """Find the standard Username-Password-Authentication connection id.

        Prefers the exact name; falls back to the first strategy=auth0 conn.
        """
        mgmt = await self._client()
        try:
            conns = await self._call(
                mgmt.connections.all, strategy="auth0", fields=["id", "name"], include_fields=True
            )
        except Auth0Error as exc:
            log.warning("getDefaultDatabaseConnectionId failed [%s]", exc.status_code)
            return None
        if not isinstance(conns, list) or not conns:
            log.warning("No auth0-strategy connections found in tenant")
            return None
        for node in conns:
            if node.get("name") == "Username-Password-Authentication":
                return node.get("id")
        return conns[0].get("id")

    async def enable_connection_on_organization(
        self, org_id: str, connection_id: str, auto_membership: bool
    ) -> None:
        mgmt = await self._client()
        body = {"connection_id": connection_id, "assign_membership_on_login": auto_membership}
        try:
            await self._call(mgmt.organizations.create_organization_connection, org_id, body)
        except Auth0Error as exc:
            raise _mgmt_error("enable connection on org", exc)
        log.info("Enabled connection '%s' on org '%s' (auto-membership=%s)",
                 connection_id, org_id, auto_membership)

    # ── Organizations ─────────────────────────────────────────────────

    async def create_organization(self, name: str, display_name: str) -> str:
        """Create an org and auto-enable the default DB connection.

        Without an enabled connection, invitation links fail (Auth0 has no way
        to authenticate the invited user). auto-membership is false so only
        explicitly invited users join.
        """
        mgmt = await self._client()
        try:
            org = await self._call(
                mgmt.organizations.create_organization,
                {"name": name, "display_name": display_name},
            )
        except Auth0Error as exc:
            raise _mgmt_error("create organization", exc)
        org_id = (org or {}).get("id")
        if not org_id:
            raise RuntimeError("Auth0 returned no organization ID")
        log.info("Created organization '%s' (slug: %s) id=%s", display_name, name, org_id)
        # Auto-enable the default DB connection so invitations work immediately.
        try:
            connection_id = await self.get_default_database_connection_id()
            if connection_id:
                await self.enable_connection_on_organization(org_id, connection_id, False)
            else:
                log.warning("No default DB connection found — org '%s' has none enabled. "
                            "Invited users will not be able to authenticate.", org_id)
        except Exception as exc:  # noqa: BLE001 - don't fail org creation
            log.error("Could not enable connection on org '%s': %s", org_id, exc)
        return org_id

    async def list_organizations_for_user(self, user_id: str) -> List[OrgSummary]:
        """List the orgs a user belongs to. Requires read:organizations."""
        mgmt = await self._client()
        try:
            body = await self._call(mgmt.users.list_organizations, user_id)
        except Auth0Error as exc:
            log.warning("listOrganizationsForUser failed [%s] for user %s",
                        exc.status_code, user_id)
            return []
        return _to_org_summaries(body)

    # ── Invitations ───────────────────────────────────────────────────

    async def invite_user_to_organization(
        self, org_id: str, inviter_name: str, invitee_email: str, client_id: str
    ) -> None:
        mgmt = await self._client()
        body = {
            "inviter": {"name": inviter_name},
            "invitee": {"email": invitee_email},
            "client_id": client_id,
            "send_invitation_email": True,
        }
        try:
            await self._call(mgmt.organizations.create_organization_invitation, org_id, body)
        except Auth0Error as exc:
            raise _mgmt_error("send invitation", exc)
        log.info("Invitation sent to '%s' for org '%s'", invitee_email, org_id)

    # ── Members ────────────────────────────────────────────────────────

    async def add_member_to_organization(self, org_id: str, user_id: str) -> None:
        """Add a member. Requires create:organization_members."""
        mgmt = await self._client()
        try:
            await self._call(
                mgmt.organizations.create_organization_members, org_id, {"members": [user_id]}
            )
        except Auth0Error as exc:
            raise _mgmt_error("add member to org", exc)
        log.info("Added member %s to org %s", user_id, org_id)

    # ── Org member roles ──────────────────────────────────────────────

    async def list_tenant_roles(self) -> List[OrgRole]:
        mgmt = await self._client()
        try:
            body = await self._call(mgmt.roles.list, per_page=100)
        except Auth0Error as exc:
            log.warning("listTenantRoles failed [%s]", exc.status_code)
            return []
        return _to_roles(body)

    async def get_roles_for_org_member(self, org_id: str, user_id: str) -> List[OrgRole]:
        mgmt = await self._client()
        try:
            body = await self._call(
                mgmt.organizations.all_organization_member_roles, org_id, user_id
            )
        except Auth0Error as exc:
            log.warning("getRolesForOrgMember failed [%s] org=%s user=%s",
                        exc.status_code, org_id, user_id)
            return []
        return _to_roles(body)

    async def list_org_members_with_roles(self, org_id: str) -> List[OrgMember]:
        mgmt = await self._client()
        try:
            body = await self._call(
                mgmt.organizations.all_organization_members,
                org_id, per_page=100, page=0, include_totals=False,
            )
        except Auth0Error as exc:
            log.warning("listOrgMembersWithRoles failed [%s] org=%s", exc.status_code, org_id)
            return []
        arr = body.get("members") if isinstance(body, dict) else body
        if not isinstance(arr, list):
            return []
        members: List[OrgMember] = []
        for node in arr:
            user_id = node.get("user_id")
            if not user_id:
                continue
            try:
                roles = await self.get_roles_for_org_member(org_id, user_id)
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not fetch roles for member %s in org %s: %s",
                            user_id, org_id, exc)
                roles = []
            members.append(OrgMember(
                user_id=user_id,
                name=node.get("name", ""),
                email=node.get("email", ""),
                picture=node.get("picture"),
                roles=roles,
            ))
        return members

    async def assign_roles_to_org_member(
        self, org_id: str, user_id: str, role_ids: List[str]
    ) -> None:
        if not role_ids:
            return
        mgmt = await self._client()
        try:
            await self._call(
                mgmt.organizations.create_organization_member_roles,
                org_id, user_id, {"roles": role_ids},
            )
        except Auth0Error as exc:
            raise _mgmt_error("assign roles", exc)
        log.info("Assigned %d role(s) to user %s in org %s", len(role_ids), user_id, org_id)

    async def remove_roles_from_org_member(
        self, org_id: str, user_id: str, role_ids: List[str]
    ) -> None:
        if not role_ids:
            return
        mgmt = await self._client()
        try:
            await self._call(
                mgmt.organizations.delete_organization_member_roles,
                org_id, user_id, {"roles": role_ids},
            )
        except Auth0Error as exc:
            raise _mgmt_error("remove roles", exc)
        log.info("Removed %d role(s) from user %s in org %s", len(role_ids), user_id, org_id)


# ── Helpers ─────────────────────────────────────────────────────────────

class ManagementApiError(RuntimeError):
    def __init__(self, action: str, status_code: int):
        self.status_code = status_code
        super().__init__(f"Failed to {action} [{status_code}]")


def _mgmt_error(action: str, exc: Auth0Error) -> ManagementApiError:
    # Log details server-side only; never echo Auth0's body to the client.
    status = getattr(exc, "status_code", 0) or 0
    log.error("Management API error during '%s' [%s]: %s",
              action, status, str(getattr(exc, "message", exc))[:300])
    return ManagementApiError(action, status)


def _to_org_summaries(body) -> List[OrgSummary]:
    arr = body if isinstance(body, list) else (body or {}).get("organizations", [])
    out: List[OrgSummary] = []
    for node in arr or []:
        oid = node.get("id")
        if oid:
            out.append(OrgSummary(
                id=oid,
                name=node.get("name", ""),
                display_name=node.get("display_name", ""),
                selected_plan=((node.get("metadata") or {}).get("selected_plan")),
            ))
    return out


def _to_roles(body) -> List[OrgRole]:
    arr = body if isinstance(body, list) else (body or {}).get("roles", [])
    out: List[OrgRole] = []
    for node in arr or []:
        rid = node.get("id")
        if rid:
            out.append(OrgRole(id=rid, name=node.get("name", ""),
                               description=node.get("description", "")))
    return out


_service: Optional[ManagementService] = None


def get_mgmt_service() -> ManagementService:
    global _service
    if _service is None:
        _service = ManagementService(get_settings(), get_token_provider())
    return _service
