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

  return (
    <div className="container">
      <h2 className="section-title">Organization roles</h2>
      {msg && <div className={`notice ${msg.kind}`}>{msg.text}</div>}
      <label>Organization</label>
      <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
        {orgs.length === 0 && <option value="">No organizations yet</option>}
        {orgs.map((o) => (
          <option key={o.id} value={o.id}>
            {o.display_name || o.name}
          </option>
        ))}
      </select>

      <table style={{ marginTop: 16 }}>
        <thead>
          <tr>
            <th>Member</th>
            {tenantRoles.map((r) => (
              <th key={r.id}>{r.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {members.map((m) => (
            <tr key={m.user_id}>
              <td>
                <div style={{ fontWeight: 600 }}>{m.name || m.user_id}</div>
                <div className="muted" style={{ fontSize: 12 }}>
                  {m.email}
                </div>
              </td>
              {tenantRoles.map((r) => {
                const has = m.roles.some((x) => x.id === r.id);
                return (
                  <td key={r.id}>
                    <button
                      className={`btn ${has ? "" : "ghost"}`}
                      style={{ padding: "4px 10px", fontSize: 12 }}
                      onClick={() => toggle(m, r)}
                    >
                      {has ? "Assigned" : "Assign"}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
          {members.length === 0 && (
            <tr>
              <td colSpan={1 + tenantRoles.length} className="muted">
                No members to display (or you lack read access).
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
