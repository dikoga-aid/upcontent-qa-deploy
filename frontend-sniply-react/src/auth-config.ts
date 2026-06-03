// Least-privilege scope list requested by the SPA. Standard OIDC scopes plus
// the API permissions the UI actually exercises. Auth0 grants the subset the
// user is authorized for (via RBAC roles); the backend enforces the rest.
export const API_SCOPES = [
  "openid",
  "profile",
  "email",
  "offline_access", // refresh tokens
  "read:organization",
  "create:organization",
].join(" ");

export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    scope: API_SCOPES,
  },
  // Persist tokens so the session survives a full page refresh (silent iframe
  // re-auth is unreliable on localhost with third-party-cookie blocking). XSS
  // risk is mitigated by the strict CSP + rotating refresh tokens w/ reuse detection.
  cacheLocation: "localstorage" as const,
  // Rotating refresh tokens (with reuse detection in Auth0) are the SOLE
  // renewal mechanism — no deprecated iframe/silent-auth fallback. A scope
  // change requires one fresh login to mint a refresh token covering it.
  useRefreshTokens: true,
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
