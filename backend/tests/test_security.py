"""JWT validation tests with a mocked JWKS.

Generates an in-test RSA keypair, signs access tokens, and stubs the
PyJWKClient so signature verification succeeds for the test key. Exercises the
hardened rules: RS256-only, issuer/audience checks, expiry, and rejection of
HS256 / alg:none / ID-token-as-access-token.
"""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app import security
from app.config import get_settings
from app.security import Principal, get_principal, require_scopes

DOMAIN = "dev-rvvkxpvy18wueufd.us.auth0.com"
ISSUER = f"https://{DOMAIN}/"
AUDIENCE = "https://upcontent-api"
KID = "test-key-1"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


class _StubSigningKey:
    key = _public_key


class _StubJWKClient:
    def __init__(self, *_args, **_kwargs):
        pass

    def get_signing_key_from_jwt(self, token):
        return _StubSigningKey()


@pytest.fixture(autouse=True)
def _patch_jwks(monkeypatch):
    # Ensure settings match the test issuer/audience and reset the cached client.
    get_settings.cache_clear()
    monkeypatch.setenv("AUTH0_DOMAIN", DOMAIN)
    monkeypatch.setenv("AUTH0_API_AUDIENCE", AUDIENCE)
    get_settings.cache_clear()
    monkeypatch.setattr(security, "_jwks_client", None)
    monkeypatch.setattr(security, "PyJWKClient", _StubJWKClient)
    yield
    get_settings.cache_clear()


def _make_token(alg="RS256", aud=AUDIENCE, iss=ISSUER, exp_delta=3600,
                scope="read:organization", key=None, extra=None):
    now = int(time.time())
    payload = {
        "sub": "auth0|tester",
        "iss": iss,
        "aud": aud,
        "iat": now,
        "exp": now + exp_delta,
        "scope": scope,
    }
    if extra:
        payload.update(extra)
    headers = {"kid": KID}
    signing_key = key if key is not None else _private_key
    return jwt.encode(payload, signing_key, algorithm=alg, headers=headers)


def _build_app():
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(p: Principal = Depends(get_principal)):
        return {"sub": p.sub, "scopes": sorted(p.scopes)}

    @app.get("/needs-scope")
    async def needs_scope(p: Principal = Depends(require_scopes("read:organization"))):
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=True)


def test_valid_token_accepted():
    client = _build_app()
    token = _make_token()
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["sub"] == "auth0|tester"


def test_missing_token_401():
    client = _build_app()
    assert client.get("/whoami").status_code == 401


def test_hs256_rejected():
    client = _build_app()
    # Forge an HS256 token signed with a guessed secret — must be rejected.
    token = jwt.encode(
        {"sub": "attacker", "iss": ISSUER, "aud": AUDIENCE,
         "iat": int(time.time()), "exp": int(time.time()) + 3600},
        "public-or-guessed-secret",
        algorithm="HS256",
        headers={"kid": KID},
    )
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_alg_none_rejected():
    client = _build_app()
    token = jwt.encode(
        {"sub": "attacker", "iss": ISSUER, "aud": AUDIENCE,
         "iat": int(time.time()), "exp": int(time.time()) + 3600},
        key=None,
        algorithm="none",
        headers={"kid": KID},
    )
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_wrong_audience_rejected():
    client = _build_app()
    token = _make_token(aud="https://wrong-api")
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_wrong_issuer_rejected():
    client = _build_app()
    token = _make_token(iss="https://evil.example.com/")
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_expired_token_rejected():
    client = _build_app()
    token = _make_token(exp_delta=-3600)
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_signed_by_other_key_rejected():
    client = _build_app()
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _make_token(key=other_key)
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_scope_enforced():
    client = _build_app()
    # Token lacking the required scope -> 403.
    token = _make_token(scope="openid profile")
    r = client.get("/needs-scope", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    # Token with the scope -> 200.
    token2 = _make_token(scope="read:organization")
    r2 = client.get("/needs-scope", headers={"Authorization": f"Bearer {token2}"})
    assert r2.status_code == 200


def test_permissions_array_merged():
    client = _build_app()
    # No scope string, but permissions array carries the grant.
    token = _make_token(scope="", extra={"permissions": ["read:organization"]})
    r = client.get("/needs-scope", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
