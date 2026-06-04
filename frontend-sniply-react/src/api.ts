import { API_BASE_URL } from "./auth-config";

// Shared API helper. Attaches the user access token as a Bearer header.
// On 401 the caller is sent back to
// login; on 403 a "missing permission/role" notice is surfaced.
export type TokenGetter = () => Promise<string>;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  getToken: TokenGetter,
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const token = await getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  let data: any = null;
  try {
    data = await res.json();
  } catch {
    /* no body */
  }
  if (!res.ok) {
    const detail = (data && data.detail) || res.statusText;
    throw new ApiError(res.status, detail);
  }
  return data as T;
}

// Sniply authenticates against its own API audience (https://sniply-api) with no
// org scopes, so it only reads identity + the org context the post-login action
// stamped into the token. Org/plan/role *management* lives in UpContent.
export interface Me {
  sub: string;
  org_id: string | null;
  org_name: string | null;
  plan: string | null;
  roles: string[];
  permissions: string[];
  email: string | null;
  name: string | null;
}

export const api = {
  me: (t: TokenGetter) => request<Me>(t, "GET", "/api/me"),
};
