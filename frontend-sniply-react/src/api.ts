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

export interface OrgSummary {
  id: string;
  name: string;
  display_name: string;
  selected_plan: string | null;
}
export interface Plan {
  id: string;
  display_name: string;
  description: string;
  price: string;
}
export interface OrgRole {
  id: string;
  name: string;
  description: string;
}
export interface OrgMember {
  user_id: string;
  name: string;
  email: string;
  picture: string | null;
  roles: OrgRole[];
}

export const api = {
  me: (t: TokenGetter) => request<any>(t, "GET", "/api/me"),
  plans: (t: TokenGetter) => request<Plan[]>(t, "GET", "/api/plans"),
  listOrgs: (t: TokenGetter) => request<OrgSummary[]>(t, "GET", "/api/organizations"),
  createOrg: (t: TokenGetter, name: string, display_name: string) =>
    request<OrgSummary>(t, "POST", "/api/organizations", { name, display_name }),
  selectPlan: (t: TokenGetter, org_id: string, plan: string) =>
    request<any>(t, "POST", "/api/plan/select", { org_id, plan }),
  invite: (t: TokenGetter, orgId: string, email: string, inviter_name?: string) =>
    request<any>(t, "POST", `/api/organizations/${orgId}/invitations`, {
      email,
      inviter_name,
    }),
  listRoles: (t: TokenGetter, orgId: string) =>
    request<{ org_id: string; members: OrgMember[]; tenant_roles: OrgRole[] }>(
      t,
      "GET",
      `/api/organizations/${orgId}/roles`,
    ),
  assignRoles: (t: TokenGetter, orgId: string, user_id: string, role_ids: string[]) =>
    request<any>(t, "POST", `/api/organizations/${orgId}/roles/assign`, {
      user_id,
      role_ids,
    }),
  removeRoles: (t: TokenGetter, orgId: string, user_id: string, role_ids: string[]) =>
    request<any>(t, "POST", `/api/organizations/${orgId}/roles/remove`, {
      user_id,
      role_ids,
    }),
};
