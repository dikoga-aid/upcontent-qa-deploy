import { useEffect, useState } from "react";
import { api, OrgSummary } from "../api";
import { useTokenGetter } from "../useApi";

// Organizations: create, list (filtered to caller server-side), invite.
export default function Organizations() {
  const getToken = useTokenGetter();
  const [orgs, setOrgs] = useState<OrgSummary[]>([]);
  const [slug, setSlug] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [inviteOrg, setInviteOrg] = useState("");
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState<{ kind: string; text: string } | null>(null);

  const reload = async () => setOrgs(await api.listOrgs(getToken));
  useEffect(() => {
    reload().catch((e) => setMsg({ kind: "error", text: e.message }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getToken]);

  const create = async () => {
    try {
      await api.createOrg(getToken, slug, displayName);
      setMsg({ kind: "success", text: `Created organization "${displayName}".` });
      setSlug("");
      setDisplayName("");
      await reload();
    } catch (e: any) {
      setMsg({ kind: "error", text: e.message });
    }
  };

  const invite = async () => {
    try {
      await api.invite(getToken, inviteOrg, email);
      setMsg({ kind: "success", text: `Invitation sent to ${email}.` });
      setEmail("");
    } catch (e: any) {
      setMsg({ kind: "error", text: e.message });
    }
  };

  return (
    <div className="container">
      <h2 className="section-title">Organizations</h2>
      {msg && <div className={`notice ${msg.kind}`}>{msg.text}</div>}
      <div className="grid cols-2">
        <div className="card">
          <h3>Create organization</h3>
          <label>Slug (lowercase, 3-50 chars)</label>
          <input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="acme-team" />
          <label>Display name</label>
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Acme Team"
          />
          <button className="btn" style={{ marginTop: 12 }} onClick={create}>
            Create
          </button>
        </div>
        <div className="card">
          <h3>Invite a member</h3>
          <label>Organization</label>
          <select value={inviteOrg} onChange={(e) => setInviteOrg(e.target.value)}>
            <option value="">Select an organization</option>
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.display_name || o.name}
              </option>
            ))}
          </select>
          <label>Invitee email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="teammate@example.com" />
          <button className="btn" style={{ marginTop: 12 }} onClick={invite} disabled={!inviteOrg}>
            Send invitation
          </button>
        </div>
      </div>

      <h2 className="section-title">Your organizations</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>ID</th>
            <th>Plan</th>
          </tr>
        </thead>
        <tbody>
          {orgs.map((o) => (
            <tr key={o.id}>
              <td>{o.display_name || o.name}</td>
              <td>
                <code>{o.id}</code>
              </td>
              <td>{o.selected_plan || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
