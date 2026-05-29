"""Machine-to-Machine token provider for the Auth0 Management API.

Fetches a token via the client_credentials grant (audience
``https://{domain}/api/v2/``), caches it in-process, and refreshes 60s before
expiry. An ``asyncio.Lock`` ensures only one refresh happens at a time.

The M2M secret is read from config (backend env only) and is NEVER logged.
"""
import asyncio
import logging
import time
from typing import Optional

import httpx

from .config import Settings, get_settings

log = logging.getLogger("upcontent.mgmt_token")

# Refresh this many seconds before the token actually expires.
_REFRESH_SKEW_SECONDS = 60


class ManagementTokenProvider:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        # Fast path: cached and not near expiry.
        if self._token and time.time() < self._expires_at - _REFRESH_SKEW_SECONDS:
            return self._token
        async with self._lock:
            # Re-check inside the lock in case another coroutine refreshed.
            if self._token and time.time() < self._expires_at - _REFRESH_SKEW_SECONDS:
                return self._token
            await self._fetch_new_token()
            return self._token  # type: ignore[return-value]

    async def _fetch_new_token(self) -> None:
        s = self._settings
        # Dict payload (never f-string JSON) — injection-safe.
        payload = {
            "client_id": s.auth0_mgmt_client_id,
            "client_secret": s.auth0_mgmt_client_secret,
            "audience": s.mgmt_audience,
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.post(f"https://{s.auth0_domain}/oauth/token", json=payload)
        if resp.status_code != 200:
            # Do not log the secret or full body; just the status.
            log.error("Failed to fetch M2M token: status=%s", resp.status_code)
            raise RuntimeError(f"Failed to fetch M2M token: {resp.status_code}")
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + int(data.get("expires_in", 86400))
        log.info("Obtained fresh Management API token (expires_in=%ss)",
                 data.get("expires_in"))


_provider: Optional[ManagementTokenProvider] = None


def get_token_provider() -> ManagementTokenProvider:
    global _provider
    if _provider is None:
        _provider = ManagementTokenProvider(get_settings())
    return _provider
