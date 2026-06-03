// Least-privilege scopes — identical to the UpContent SPA (same Auth0 API).
export const API_SCOPES = [
  "openid",
  "profile",
  "email",
  "offline_access",
  "read:organization",
  "create:organization",
].join(" ");

export const auth0Options = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    scope: API_SCOPES,
  },
  // Persist tokens so the session survives a full page refresh. XSS risk is
  // mitigated by the strict CSP + rotating refresh tokens with reuse detection.
  cacheLocation: "localstorage" as const,
  // Rotating refresh tokens are the SOLE renewal mechanism — no deprecated
  // iframe/silent-auth fallback. A scope change requires one fresh login.
  useRefreshTokens: true,
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
