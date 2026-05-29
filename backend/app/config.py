"""Application configuration, loaded from environment / .env via pydantic-settings.

Mirrors the reference apps' discipline of keeping all environment-specific values
out of code. The M2M secret lives here (backend env only) and is NEVER logged.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Auth0 tenant / API ────────────────────────────────────────────
    auth0_domain: str = "dev-rvvkxpvy18wueufd.us.auth0.com"
    # The audience of THIS resource server (the Auth0 API identifier).
    auth0_api_audience: str = "https://upcontent-api"

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
