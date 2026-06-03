import { useEffect, useState } from "react";
import { api, OrgMember, OrgRole, OrgSummary } from "../api";
import { useTokenGetter } from "../useApi";

// Org Roles: list members + their roles, assign/remove tenant roles.
// Backend requires admin of the org for assign/remove (object-level check).
export default function Roles() {
  const getToken = useTokenGetter();
  const [orgs, setOrgs] = useState<OrgSummary[]>([]);
  const [orgId, setOrgId] = useState("");
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [tenantRoles, setTenantRoles] = useState<OrgRole[]>([]);
  const [msg, setMsg] = useState<{ kind: string; text: string } | null>(null);

  useEffect(() => {
    api
      .listOrgs(getToken)
      .then((o) => {
        setOrgs(o);
        if (o.length && !orgId) setOrgId(o[0].id);
      })
      .catch((e) => setMsg({ kind: "error", text: e.message }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getToken]);

  const load = async (id: string) => {
    try {
      const data = await api.listRoles(getToken, id);
      setMembers(data.members);
      setTenantRoles(data.tenant_roles);
    } catch (e: any) {
      setMsg({ kind: "error", text: e.message });
    }
  };

  useEffect(() => {
    if (orgId) load(orgId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  const toggle = async (m: OrgMember, role: OrgRole) => {
    const has = m.roles.some((r) => r.id === role.id);
    try {
      if (has) await api.removeRoles(getToken, orgId, m.user_id, [role.id]);
      else await api.assignRoles(getToken, orgId, m.user_id, [role.id]);
      setMsg({
        kind: "success",
        text: `${has ? "Removed" : "Assigned"} "${role.name}".`,
      });
      await load(orgId);
    } catch (e: any) {
      setMsg({ kind: "error", text: e.message });
    }
  };

  const orgName = orgs.find((o) => o.id === orgId);
  const orgLabel = orgName ? orgName.display_name || orgName.name : "";

  return (
    <main className="page-main">
      <header className="page-header">
        <h1 className="page-title">
          {orgLabel || "Organization"}
          <span style={{ color: "var(--text-3)", fontSize: 24 }}> / Roles</span>
        </h1>
        <p className="page-sub">
          Manage role assignments for members of this organization.
        </p>
      </header>

      {msg && <div className={`alert alert-${msg.kind}`}>{msg.text}</div>}

      <div className="org-selector-wrap">
        <label className="form-label" htmlFor="rolesOrg">
          Organization
        </label>
        <select
          className="form-input form-select"
          id="rolesOrg"
          style={{ maxWidth: 400 }}
          value={orgId}
          onChange={(e) => setOrgId(e.target.value)}
        >
          {orgs.length === 0 && <option value="">No organizations yet</option>}
          {orgs.map((o) => (
            <option key={o.id} value={o.id}>
              {o.display_name || o.name}
            </option>
          ))}
        </select>
      </div>

      <section className="card card-wide">
        <div className="section-header" style={{ marginBottom: 20 }}>
          <span className="section-icon">👥</span>
          <h2 className="card-title">Members &amp; roles</h2>
          <span className="badge badge--neutral" style={{ marginLeft: 8 }}>
            {members.length} member{members.length === 1 ? "" : "s"}
          </span>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Member</th>
              <th>Current roles</th>
              <th>Assign roles</th>
              <th>User ID</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.user_id}>
                <td>
                  <div className="member-cell">
                    {m.picture ? (
                      <img className="member-avatar" src={m.picture} alt="" />
                    ) : (
                      <div className="member-avatar-initials">
                        {(m.name || m.email || "?").substring(0, 1).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 500 }}>
                        {m.name || m.email}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--text-3)" }}>
                        {m.email}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  {m.roles.length === 0 ? (
                    <span style={{ fontSize: 13, color: "var(--text-3)" }}>
                      No roles assigned
                    </span>
                  ) : (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {m.roles.map((role) => (
                        <span className="role-chip" key={role.id}>
                          <span>{role.name}</span>
                          <button
                            title="Remove role"
                            onClick={() => toggle(m, role)}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </td>
                <td>
                  {tenantRoles.length === 0 ? (
                    <span style={{ fontSize: 13, color: "var(--text-3)" }}>
                      No roles available
                    </span>
                  ) : (
                    <div className="assign-checks">
                      {tenantRoles.map((role) => {
                        const has = m.roles.some((r) => r.id === role.id);
                        return (
                          <label key={role.id} title={role.description}>
                            <input
                              type="checkbox"
                              checked={has}
                              onChange={() => toggle(m, role)}
                            />
                            <span>{role.name}</span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </td>
                <td>
                  <code style={{ fontSize: 11 }}>{m.user_id}</code>
                </td>
              </tr>
            ))}
            {members.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: "var(--text-2)" }}>
                  No members to display (or you lack read access).
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
