"""Application configuration, loaded from environment / .env via pydantic-settings.

All environment-specific values live here, not in code. The M2M secret is read
from the backend environment only and is NEVER logged.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Namespace the "Add Custom Claims" post-login Action stamps custom claims under
# (org_id/org_name/plan/roles, and pending_plan from the signup `selected-plan`).
# Must match the namespace used in the Action code.
CLAIMS_NAMESPACE = "https://upcontent.com"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Auth0 tenant / API ────────────────────────────────────────────
    # Tenant domain (e.g. "your-tenant.us.auth0.com"). Required — from env/.env.
    auth0_domain: str
    # Accepted audiences for THIS resource server. Comma-separated to allow the
    # per-app API split: UpContent SPA -> https://upcontent-api, Sniply SPA ->
    # https://sniply-api. A token is accepted if its `aud` matches any listed value.
    # (The Sniply API has no scopes yet, so Sniply's scope-gated routes 403 until
    # read:organization / create:organization are added to it.)
    auth0_api_audience: str = "https://upcontent-api,https://sniply-api"

    # ── M2M client (server-side only) used to mint Management API tokens ──
    auth0_mgmt_client_id: str = ""
    auth0_mgmt_client_secret: str = ""

    # SPA client_id used when sending org invitations (so the invite link
    # targets the right application). Optional; falls back to mgmt client.
    auth0_spa_client_id: str = ""

    # ── Server ────────────────────────────────────────────────────────
    port: int = 5000
    # Strict CORS allow-list — comma-separated; the two Vite dev origins. No "*".
    # Stored as a raw string (pydantic-settings would otherwise JSON-parse a
    # List[str] env value); parsed via the `allowed_origins` property.
    allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        validation_alias="ALLOWED_ORIGINS",
    )
    # Enable HSTS only behind TLS in production.
    production: bool = False

    @property
    def allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins_raw.split(",") if o.strip()]

    @property
    def auth0_api_audiences(self) -> List[str]:
        """Accepted token audiences (the per-app API identifiers)."""
        return [a.strip() for a in self.auth0_api_audience.split(",") if a.strip()]

    # ── Derived values ────────────────────────────────────────────────
    @property
    def issuer(self) -> str:
        return f"https://{self.auth0_domain}/"

    @property
    def jwks_url(self) -> str:
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    @property
    def mgmt_audience(self) -> str:
        return f"https://{self.auth0_domain}/api/v2/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
