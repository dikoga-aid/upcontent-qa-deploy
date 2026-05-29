// Least-privilege scope list requested by the SPA. Standard OIDC scopes plus
// the API permissions the UI actually exercises. Auth0 grants the subset the
// user is authorized for (via RBAC roles); the backend enforces the rest.
export const API_SCOPES = [
  "openid",
  "profile",
  "email",
  "offline_access", // refresh tokens
  "read:organizations",
  "create:organizations",
  "update:organizations",
  "create:organization_invitations",
  "read:organization_members",
  "create:organization_member_roles",
  "delete:organization_member_roles",
].join(" ");

export const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    scope: API_SCOPES,
  },
  // Access token in memory only (never localStorage) — XSS-resistant.
  cacheLocation: "memory" as const,
  // Refresh tokens (rotating, with reuse detection enabled in Auth0).
  useRefreshTokens: true,
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
