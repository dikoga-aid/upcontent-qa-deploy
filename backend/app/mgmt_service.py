"""Auth0 Management API client.

JSON payloads are built as Python dicts (never via string formatting) so
special characters in user-supplied values cannot inject malformed JSON. httpx
is configured with explicit timeouts so requests never hang indefinitely.

Every path segment that originates from user input is validated upstream
(see ``validators.py``) and URL-encoded here before interpolation.
"""
import logging
from typing import List, Optional

import httpx

from .config import Settings, get_settings
from .mgmt_token import ManagementTokenProvider, get_token_provider
from .models import OrgMember, OrgRole, OrgSummary
from .validators import url_encode

log = logging.getLogger("upcontent.mgmt_service")

_TIMEOUT = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)


class ManagementService:
    def __init__(self, settings: Settings, token_provider: ManagementTokenProvider):
        self._s = settings
        self._tokens = token_provider

    @property
    def _base(self) -> str:
        return f"https://{self._s.auth0_domain}/api/v2"

    async def _client(self) -> httpx.AsyncClient:
        token = await self._tokens.get_token()
        return httpx.AsyncClient(
            base_url=self._base,
            timeout=_TIMEOUT,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    # ── Organization plan (metadata) ──────────────────────────────────

    async def update_org_plan(self, org_id: str, plan: str) -> None:
        """PATCH org metadata.selected_plan. Requires update:organizations."""
        payload = {"metadata": {"selected_plan": plan}}
        async with await self._client() as client:
            resp = await client.patch(f"/organizations/{org_id}", json=payload)
        if resp.status_code >= 300:
            raise _mgmt_error("update org plan", resp)
        log.info("Updated plan for org %s to '%s'", org_id, plan)

    async def get_org_plan(self, org_id: str) -> Optional[str]:
        """GET org and read metadata.selected_plan. Requires read:organizations."""
        async with await self._client() as client:
            resp = await client.get(f"/organizations/{org_id}")
        if resp.status_code >= 300:
            log.warning("Could not fetch org [%s] for plan lookup: %s", org_id, resp.status_code)
            return None
        meta = (resp.json() or {}).get("metadata") or {}
        return meta.get("selected_plan")

    # ── Connections ───────────────────────────────────────────────────

    async def get_default_database_connection_id(self) -> Optional[str]:
        """Find the standard Username-Password-Authentication connection id.

        Prefers the exact name; falls back to the first strategy=auth0 conn.
        """
        params = {
            "strategy": "auth0",
            "fields": "id,name",
            "include_fields": "true",
            "per_page": "100",
            "page": "0",
        }
        async with await self._client() as client:
            resp = await client.get("/connections", params=params)
        if resp.status_code >= 300:
            log.warning("getDefaultDatabaseConnectionId failed [%s]", resp.status_code)
            return None
        arr = resp.json()
        if not isinstance(arr, list) or not arr:
            log.warning("No auth0-strategy connections found in tenant")
            return None
        for node in arr:
            if node.get("name") == "Username-Password-Authentication":
                return node.get("id")
        return arr[0].get("id")

    async def enable_connection_on_organization(
        self, org_id: str, connection_id: str, auto_membership: bool
    ) -> None:
        payload = {"connection_id": connection_id, "assign_membership_on_login": auto_membership}
        async with await self._client() as client:
            resp = await client.post(f"/organizations/{org_id}/enabled_connections", json=payload)
        if resp.status_code >= 300:
            raise _mgmt_error("enable connection on org", resp)
        log.info("Enabled connection '%s' on org '%s' (auto-membership=%s)",
                 connection_id, org_id, auto_membership)

    # ── Organizations ─────────────────────────────────────────────────

    async def create_organization(self, name: str, display_name: str) -> str:
        """Create an org and auto-enable the default DB connection.

        Without an enabled connection, invitation links fail (Auth0 has no way
        to authenticate the invited user). auto-membership is false so only
        explicitly invited users join.
        """
        payload = {"name": name, "display_name": display_name}
        async with await self._client() as client:
            resp = await client.post("/organizations", json=payload)
        if resp.status_code >= 300:
            raise _mgmt_error("create organization", resp)
        org_id = (resp.json() or {}).get("id")
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
        """GET /users/{id}/organizations. Requires read:organizations."""
        async with await self._client() as client:
            resp = await client.get(
                f"/users/{url_encode(user_id)}/organizations",
                params={"per_page": "50", "page": "0"},
            )
        if resp.status_code >= 300:
            log.warning("listOrganizationsForUser failed [%s] for user %s",
                        resp.status_code, user_id)
            return []
        return _to_org_summaries(resp.json())

    # ── Invitations ───────────────────────────────────────────────────

    async def invite_user_to_organization(
        self, org_id: str, inviter_name: str, invitee_email: str, client_id: str
    ) -> None:
        payload = {
            "inviter": {"name": inviter_name},
            "invitee": {"email": invitee_email},
            "client_id": client_id,
            "send_invitation_email": True,
        }
        async with await self._client() as client:
            resp = await client.post(f"/organizations/{org_id}/invitations", json=payload)
        if resp.status_code >= 300:
            raise _mgmt_error("send invitation", resp)
        log.info("Invitation sent to '%s' for org '%s'", invitee_email, org_id)

    # ── Members ────────────────────────────────────────────────────────

    async def add_member_to_organization(self, org_id: str, user_id: str) -> None:
        """POST /organizations/{org_id}/members. Requires create:organization_members.

        user_id goes in the JSON body (not the URL), so no path-encoding is
        needed; the dict payload is injection-safe.
        """
        payload = {"members": [user_id]}
        async with await self._client() as client:
            resp = await client.post(f"/organizations/{org_id}/members", json=payload)
        if resp.status_code >= 300:
            raise _mgmt_error("add member to org", resp)
        log.info("Added member %s to org %s", user_id, org_id)

    # ── Org member roles ──────────────────────────────────────────────

    async def list_tenant_roles(self) -> List[OrgRole]:
        async with await self._client() as client:
            resp = await client.get("/roles", params={"per_page": "100", "page": "0"})
        if resp.status_code >= 300:
            log.warning("listTenantRoles failed [%s]", resp.status_code)
            return []
        return _to_roles(resp.json())

    async def get_roles_for_org_member(self, org_id: str, user_id: str) -> List[OrgRole]:
        async with await self._client() as client:
            resp = await client.get(
                f"/organizations/{org_id}/members/{url_encode(user_id)}/roles"
            )
        if resp.status_code >= 300:
            log.warning("getRolesForOrgMember failed [%s] org=%s user=%s",
                        resp.status_code, org_id, user_id)
            return []
        return _to_roles(resp.json())

    async def list_org_members_with_roles(self, org_id: str) -> List[OrgMember]:
        async with await self._client() as client:
            resp = await client.get(
                f"/organizations/{org_id}/members",
                params={"per_page": "100", "page": "0"},
            )
        if resp.status_code >= 300:
            log.warning("listOrgMembersWithRoles failed [%s] org=%s", resp.status_code, org_id)
            return []
        body = resp.json()
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
        payload = {"roles": role_ids}
        async with await self._client() as client:
            resp = await client.post(
                f"/organizations/{org_id}/members/{url_encode(user_id)}/roles", json=payload
            )
        if resp.status_code >= 300:
            raise _mgmt_error("assign roles", resp)
        log.info("Assigned %d role(s) to user %s in org %s", len(role_ids), user_id, org_id)

    async def remove_roles_from_org_member(
        self, org_id: str, user_id: str, role_ids: List[str]
    ) -> None:
        if not role_ids:
            return
        payload = {"roles": role_ids}
        async with await self._client() as client:
            resp = await client.request(
                "DELETE",
                f"/organizations/{org_id}/members/{url_encode(user_id)}/roles",
                json=payload,
            )
        if resp.status_code >= 300:
            raise _mgmt_error("remove roles", resp)
        log.info("Removed %d role(s) from user %s in org %s", len(role_ids), user_id, org_id)


# ── Helpers ─────────────────────────────────────────────────────────────

class ManagementApiError(RuntimeError):
    def __init__(self, action: str, status_code: int):
        self.status_code = status_code
        super().__init__(f"Failed to {action} [{status_code}]")


def _mgmt_error(action: str, resp: httpx.Response) -> ManagementApiError:
    # Log details server-side only; never echo Auth0's body to the client.
    log.error("Management API error during '%s' [%s]: %s",
              action, resp.status_code, resp.text[:300])
    return ManagementApiError(action, resp.status_code)


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
