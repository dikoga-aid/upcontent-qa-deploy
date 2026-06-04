// Sniply is an authentication-only demo against its own API audience
// (https://sniply-api), which defines no org scopes, so it requests just the
// standard OIDC scopes. Org/plan/role management (and its scopes) live in UpContent.
export const API_SCOPES = [
  "openid",
  "profile",
  "email",
  "offline_access", // refresh tokens
].join(" ");

export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    // Sniply's Auth0 client registers its callback with a trailing slash.
    redirect_uri: window.location.origin + "/",
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
