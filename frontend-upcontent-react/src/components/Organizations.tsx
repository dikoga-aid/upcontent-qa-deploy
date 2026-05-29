import { useEffect, useState } from "react";
import { api, OrgSummary } from "../api";
import { useTokenGetter } from "../useApi";

// Derive an Auth0 org slug from the display name:
// lowercase, non-alphanumerics → hyphens, trim leading/trailing hyphens.
const slugify = (s: string) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

// Organizations: create, list (filtered to caller server-side), invite.
export default function Organizations() {
  const getToken = useTokenGetter();
  const [orgs, setOrgs] = useState<OrgSummary[]>([]);
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
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
      setSlugEdited(false);
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
    <main className="page-main">
      <header className="page-header">
        <h1 className="page-title">Organization</h1>
        <p className="page-sub">Create organizations and invite team members.</p>
      </header>

      {msg && <div className={`alert alert-${msg.kind}`}>{msg.text}</div>}

      <div className="two-col">
        {/* Create organization */}
        <section className="card">
          <div className="card-header">
            <div className="card-icon">🏢</div>
            <h2 className="card-title">Create organization</h2>
            <p className="card-sub">Set up a new Auth0 organization for your team.</p>
          </div>
          <div className="form-stack">
            <div className="form-group">
              <label className="form-label" htmlFor="displayName">
                Display name
              </label>
              <input
                className="form-input"
                id="displayName"
                value={displayName}
                onChange={(e) => {
                  const v = e.target.value;
                  setDisplayName(v);
                  if (!slugEdited) setSlug(slugify(v));
                }}
                placeholder="Acme Corporation"
              />
              <span className="form-hint">Shown to users in Auth0</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="orgName">
                Organization ID (slug)
              </label>
              <input
                className="form-input"
                id="orgName"
                value={slug}
                onChange={(e) => {
                  setSlug(e.target.value);
                  setSlugEdited(true);
                }}
                placeholder="acme-corp"
              />
              <span className="form-hint">
                Lowercase, hyphens only — used in Auth0 URLs
              </span>
            </div>
            <button className="btn btn-primary btn-full" onClick={create}>
              Create organization
            </button>
          </div>
        </section>

        {/* Invite a member */}
        <section className="card">
          <div className="card-header">
            <div className="card-icon">✉️</div>
            <h2 className="card-title">Invite a member</h2>
            <p className="card-sub">Send an Auth0 invitation email to a team member.</p>
          </div>
          <div className="form-stack">
            <div className="form-group">
              <label className="form-label" htmlFor="orgSelect">
                Select organization
              </label>
              <select
                className="form-input form-select"
                id="orgSelect"
                value={inviteOrg}
                onChange={(e) => setInviteOrg(e.target.value)}
              >
                <option value="" disabled>
                  Choose an organization…
                </option>
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.display_name || o.name}
                  </option>
                ))}
              </select>
              {orgs.length === 0 && (
                <span className="form-hint">
                  No organizations yet — create one first.
                </span>
              )}
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="inviteEmail">
                Email address
              </label>
              <input
                className="form-input"
                id="inviteEmail"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="colleague@example.com"
              />
              <span className="form-hint">
                An invitation email will be sent via Auth0
              </span>
            </div>
            <button
              className="btn btn-primary btn-full"
              disabled={!inviteOrg}
              onClick={invite}
            >
              Send invitation
            </button>
          </div>
        </section>
      </div>

      {/* Existing organizations */}
      {orgs.length > 0 && (
        <section className="card card-wide">
          <div className="card-header">
            <div className="card-icon">📋</div>
            <h2 className="card-title">Existing organizations</h2>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Display name</th>
                <th>Slug</th>
                <th>Auth0 ID</th>
                <th>Plan</th>
              </tr>
            </thead>
            <tbody>
              {orgs.map((o) => (
                <tr key={o.id}>
                  <td>{o.display_name || "—"}</td>
                  <td>
                    <code>{o.name}</code>
                  </td>
                  <td>
                    <code>{o.id}</code>
                  </td>
                  <td>{o.selected_plan || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}
