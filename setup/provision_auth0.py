#!/usr/bin/env python3
"""Idempotent Auth0 provisioning for the UpContent + Sniply demo.

Attempts, via the server-side M2M client (client_credentials → Management API):
  1. Create the API (resource server) `https://upcontent-api` (RS256, RBAC on,
     "Add Permissions in the Access Token" on) with the route-table permissions.
  2. Create one SPA application (token_endpoint_auth_method=none) shared by both
     frontends, with localhost callbacks/logout/web-origins and refresh-token
     rotation + reuse detection.
  3. Create an "Org Admin" role (all permissions) and a "Member" role (reads).

If the M2M client lacks `create:clients` / `create:resource_servers` / role
scopes, the script does NOT fail: it detects the 403, prints the exact manual
Auth0 Dashboard steps, and exits 0 so it can be re-run after grants are added.

Run from the backend venv so deps (httpx) are available:
    cd backend && . .venv/bin/activate && python ../setup/provision_auth0.py
Reads AUTH0_* from backend/.env (or the environment).
"""
import os
import sys
from pathlib import Path

import httpx

# Load backend/.env if present (no python-dotenv dependency required).
ENV_PATH = Path(__file__).resolve().parent.parent / "backend" / ".env"


def _load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_env()

DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
CLIENT_ID = os.environ.get("AUTH0_MGMT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("AUTH0_MGMT_CLIENT_SECRET", "")
API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE", "https://upcontent-api")

CALLBACKS = ["http://localhost:3000", "http://localhost:3001"]

API_PERMISSIONS = [
    ("read:organizations", "List the caller's organizations"),
    ("create:organizations", "Create a new organization"),
    ("update:organizations", "Update an organization (e.g. plan)"),
    ("create:organization_invitations", "Invite a member to an organization"),
    ("read:organization_members", "Read organization members"),
    ("create:organization_member_roles", "Assign roles to org members"),
    ("delete:organization_member_roles", "Remove roles from org members"),
]
MEMBER_PERMISSIONS = {"read:organizations", "read:organization_members"}


class PermissionDenied(Exception):
    pass


def _base() -> str:
    return f"https://{DOMAIN}/api/v2"


def get_mgmt_token(client: httpx.Client) -> str:
    resp = client.post(
        f"https://{DOMAIN}/oauth/token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "audience": f"https://{DOMAIN}/api/v2/",
            "grant_type": "client_credentials",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _check(resp: httpx.Response, what: str) -> None:
    if resp.status_code == 403:
        raise PermissionDenied(what)
    if resp.status_code >= 300 and resp.status_code != 409:
        raise RuntimeError(f"{what} failed [{resp.status_code}]: {resp.text[:300]}")


def ensure_api(client: httpx.Client, headers: dict) -> None:
    # Idempotent: look up by identifier first.
    existing = client.get(f"{_base()}/resource-servers", headers=headers,
                          params={"per_page": 100})
    _check(existing, "list resource servers")
    for rs in existing.json():
        if rs.get("identifier") == API_AUDIENCE:
            print(f"  API '{API_AUDIENCE}' already exists (id={rs.get('id')}).")
            return
    payload = {
        "name": "UpContent + Sniply API",
        "identifier": API_AUDIENCE,
        "signing_alg": "RS256",
        "scopes": [{"value": v, "description": d} for v, d in API_PERMISSIONS],
        "enforce_policies": True,                 # RBAC
        "token_dialect": "access_token_authz",    # Add Permissions in Access Token
        "allow_offline_access": True,             # refresh tokens
    }
    resp = client.post(f"{_base()}/resource-servers", headers=headers, json=payload)
    _check(resp, "create resource server")
    print(f"  Created API '{API_AUDIENCE}' (RS256, RBAC, permissions in token).")


def ensure_spa(client: httpx.Client, headers: dict) -> str:
    existing = client.get(f"{_base()}/clients", headers=headers,
                          params={"per_page": 100, "fields": "client_id,name,app_type",
                                  "include_fields": "true"})
    _check(existing, "list clients")
    for c in existing.json():
        if c.get("name") == "UpContent + Sniply SPA":
            print(f"  SPA app already exists (client_id={c.get('client_id')}).")
            return c.get("client_id")
    payload = {
        "name": "UpContent + Sniply SPA",
        "app_type": "spa",
        "token_endpoint_auth_method": "none",
        "callbacks": CALLBACKS,
        "allowed_logout_urls": CALLBACKS,
        "web_origins": CALLBACKS,
        "allowed_origins": CALLBACKS,
        "oidc_conformant": True,
        "grant_types": ["authorization_code", "refresh_token"],
        "refresh_token": {
            "rotation_type": "rotating",
            "expiration_type": "expiring",
            "leeway": 0,
            "token_lifetime": 2592000,
            "infinite_token_lifetime": False,
            "idle_token_lifetime": 1296000,
            "infinite_idle_token_lifetime": False,
        },
    }
    resp = client.post(f"{_base()}/clients", headers=headers, json=payload)
    _check(resp, "create SPA client")
    client_id = resp.json().get("client_id")
    print(f"  Created SPA app (client_id={client_id}).")
    return client_id


def ensure_roles(client: httpx.Client, headers: dict) -> None:
    existing = client.get(f"{_base()}/roles", headers=headers, params={"per_page": 100})
    _check(existing, "list roles")
    by_name = {r.get("name"): r for r in existing.json()}

    def ensure_role(name: str, description: str, perms) -> None:
        role = by_name.get(name)
        if role is None:
            resp = client.post(f"{_base()}/roles", headers=headers,
                               json={"name": name, "description": description})
            _check(resp, f"create role {name}")
            role = resp.json()
            print(f"  Created role '{name}'.")
        else:
            print(f"  Role '{name}' already exists.")
        if perms:
            body = {"permissions": [
                {"resource_server_identifier": API_AUDIENCE, "permission_name": p}
                for p in perms
            ]}
            resp = client.post(f"{_base()}/roles/{role['id']}/permissions",
                               headers=headers, json=body)
            # 409/201 both fine; tolerate already-assigned.
            if resp.status_code not in (200, 201, 204, 409):
                _check(resp, f"assign permissions to {name}")

    all_perms = [v for v, _ in API_PERMISSIONS]
    ensure_role("Org Admin", "Full org administration", all_perms)
    ensure_role("Member", "Read-only org access", sorted(MEMBER_PERMISSIONS))


MANUAL_STEPS = f"""
────────────────────────────────────────────────────────────────────────
  MANUAL AUTH0 DASHBOARD STEPS (M2M lacks provisioning scopes — do these)
────────────────────────────────────────────────────────────────────────
1) APIs → Create API
     Name:        UpContent + Sniply API
     Identifier:  {API_AUDIENCE}
     Signing alg: RS256
   Then in the API's Settings:
     - Enable "RBAC"
     - Enable "Add Permissions in the Access Token"
     - Enable "Allow Offline Access" (refresh tokens)
   In the API's Permissions tab, add:
""" + "".join(f"       {v}  —  {d}\n" for v, d in API_PERMISSIONS) + f"""
2) Applications → Create Application → "Single Page Web Applications"
     Name: UpContent + Sniply SPA
   In Settings:
     Allowed Callback URLs:   {", ".join(CALLBACKS)}
     Allowed Logout URLs:     {", ".join(CALLBACKS)}
     Allowed Web Origins:     {", ".join(CALLBACKS)}
     Token Endpoint Auth Method: None
   In the "Refresh Token Rotation" section:
     - Enable "Rotation" (this turns on reuse detection)
     - Enable "Absolute Expiration"
   Copy the resulting Client ID into the frontends' .env files
   (VITE_AUTH0_CLIENT_ID) and into backend/.env (AUTH0_SPA_CLIENT_ID).

3) User Management → Roles → Create Role
     "Org Admin"  → add ALL permissions above
     "Member"     → add: {", ".join(sorted(MEMBER_PERMISSIONS))}
   Assign these roles to your test users so their access tokens carry perms.
────────────────────────────────────────────────────────────────────────
"""


def main() -> int:
    if not (DOMAIN and CLIENT_ID and CLIENT_SECRET):
        print("ERROR: AUTH0_DOMAIN / AUTH0_MGMT_CLIENT_ID / AUTH0_MGMT_CLIENT_SECRET "
              "must be set (backend/.env or env).")
        return 1

    print(f"Provisioning tenant {DOMAIN} ...")
    with httpx.Client(timeout=20.0) as client:
        try:
            token = get_mgmt_token(client)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: could not obtain Management token: {exc}")
            return 1
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        spa_client_id = None
        try:
            print("API (resource server):")
            ensure_api(client, headers)
            print("SPA application:")
            spa_client_id = ensure_spa(client, headers)
            print("Roles:")
            ensure_roles(client, headers)
        except PermissionDenied as denied:
            print(f"\n  M2M client is not authorized to '{denied}'.")
            print(MANUAL_STEPS)
            return 0

    print("\nProvisioning complete.")
    print(f"  API audience:   {API_AUDIENCE}")
    if spa_client_id:
        print(f"  SPA client_id:  {spa_client_id}")
        print("  → Put this in frontend-*/.env (VITE_AUTH0_CLIENT_ID) and "
              "backend/.env (AUTH0_SPA_CLIENT_ID).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
