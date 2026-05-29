// Least-privilege scopes — identical to the UpContent SPA (same Auth0 API).
export const API_SCOPES = [
  "openid",
  "profile",
  "email",
  "offline_access",
  "read:organizations",
  "create:organizations",
  "update:organizations",
  "create:organization_invitations",
  "read:organization_members",
  "create:organization_member_roles",
  "delete:organization_member_roles",
].join(" ");

export const auth0Options = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE,
    scope: API_SCOPES,
  },
  // Token in memory only; rotating refresh tokens.
  cacheLocation: "memory" as const,
  useRefreshTokens: true,
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
