"""FastAPI resource server entrypoint.

Wires CORS allow-list, security headers, routers, and /healthz. This service is
an Auth0-protected resource server: every /api route validates a user access
token and enforces a scope plus (for org-scoped routes) an object-level check.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routes import me, organizations, plans, roles
from .validators import ValidationError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("upcontent")

settings = get_settings()

app = FastAPI(
    title="UpContent + Sniply Identity API",
    description="Auth0-protected resource server for the UpContent/Sniply demo. "
                "DEMO — not a production system.",
    version="1.0.0",
)

# ── Strict CORS: explicit origin allow-list, no "*", no credentials ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    # Token-bearing responses must not be cached by shared caches.
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if settings.production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.exception_handler(ValidationError)
async def _validation_handler(request: Request, exc: ValidationError):
    # Generic 422; sanitized message comes from the validator itself.
    return JSONResponse(status_code=422, content={"detail": str(exc)})


app.include_router(me.router)
app.include_router(organizations.router)
app.include_router(plans.router)
app.include_router(roles.router)


@app.get("/healthz", tags=["health"])
async def healthz() -> dict:
    return {"status": "ok"}
