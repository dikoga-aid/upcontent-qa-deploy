import { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { api, OrgSummary } from "../api";
import { useTokenGetter } from "../useApi";

// Portal: profile + the permissions the token carries + the caller's orgs
// with plan badges. Demonstrates that RBAC permissions flow into the token.
export default function Portal() {
  const { user } = useAuth0();
  const getToken = useTokenGetter();
  const [perms, setPerms] = useState<string[]>([]);
  const [orgs, setOrgs] = useState<OrgSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const me = await api.me(getToken);
        setPerms(me.permissions || []);
        setOrgs(await api.listOrgs(getToken));
      } catch (e: any) {
        setError(e.message || "Failed to load portal.");
      }
    })();
  }, [getToken]);

  const name = user?.name || user?.email || "Unknown user";
  const initial = (name || "?").substring(0, 1).toUpperCase();
  const orgsWithPlan = orgs.filter((o) => o.selected_plan);

  return (
    <main className="page-main">
      {error && <div className="alert alert-error">{error}</div>}

      {/* ── Hero identity strip ── */}
      <div className="profile-hero">
        <div className="avatar-wrap">
          {user?.picture ? (
            <img src={user.picture} className="avatar-img" alt="Profile picture" />
          ) : (
            <div className="avatar-initials">{initial}</div>
          )}
          {user?.email_verified && (
            <span className="avatar-verified" title="Email verified">
              ✓
            </span>
          )}
        </div>

        <div className="profile-identity">
          <h1 className="profile-name">{name}</h1>
          <div className="profile-meta">
            {user?.email && (
              <span className="meta-pill">
                <span className="meta-icon">✉</span>
                <span>{user.email}</span>
              </span>
            )}
            {user?.sub && (
              <span className="meta-pill">
                <span className="meta-icon">#</span>
                <span>{user.sub}</span>
              </span>
            )}
            {orgsWithPlan.length === 0 ? (
              <span className="meta-pill meta-pill--warn">
                <span className="meta-icon">!</span> No plan selected
              </span>
            ) : orgsWithPlan.length === 1 ? (
              <span className="meta-pill meta-pill--plan">
                <span className="meta-icon">★</span>
                <span>{orgsWithPlan[0].selected_plan}</span>
              </span>
            ) : (
              <span className="meta-pill meta-pill--plan">
                <span className="meta-icon">★</span>
                <span>{orgsWithPlan.length} org plans active</span>
              </span>
            )}
            {orgs.length > 0 && (
              <span className="meta-pill meta-pill--org">
                <span className="meta-icon">🏢</span>
                <span>
                  {orgs.length} organization{orgs.length === 1 ? "" : "s"}
                </span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Detail grid ── */}
      <div className="portal-grid">
        {/* Profile */}
        <section className="card portal-section">
          <div className="section-header">
            <span className="section-icon">👤</span>
            <h2 className="card-title">Identity</h2>
          </div>
          <dl className="info-list">
            <div className="info-row">
              <dt>Full name</dt>
              <dd>{user?.name || "—"}</dd>
            </div>
            <div className="info-row">
              <dt>Given name</dt>
              <dd>{user?.given_name || "—"}</dd>
            </div>
            <div className="info-row">
              <dt>Family name</dt>
              <dd>{user?.family_name || "—"}</dd>
            </div>
            <div className="info-row">
              <dt>Nickname</dt>
              <dd>{user?.nickname || "—"}</dd>
            </div>
            <div className="info-row">
              <dt>Email</dt>
              <dd>{user?.email || "—"}</dd>
            </div>
            <div className="info-row">
              <dt>Email verified</dt>
              <dd>
                {user?.email_verified ? (
                  <span className="badge badge--success">Verified</span>
                ) : (
                  <span className="badge badge--warn">Not verified</span>
                )}
              </dd>
            </div>
            <div className="info-row">
              <dt>Subject</dt>
              <dd>
                <code>{user?.sub || "—"}</code>
              </dd>
            </div>
          </dl>
        </section>

        {/* Token permissions */}
        <section className="card portal-section">
          <div className="section-header">
            <span className="section-icon">🛡</span>
            <h2 className="card-title">Token permissions</h2>
          </div>
          {perms.length === 0 ? (
            <p className="card-sub">
              No permissions in token. Assign a role to your user in Auth0.
            </p>
          ) : (
            <div className="tag-cloud">
              {perms.map((p) => (
                <span className="tag" key={p}>
                  {p}
                </span>
              ))}
            </div>
          )}
        </section>

        {/* Organizations */}
        <section className="card portal-section portal-section--wide">
          <div className="section-header">
            <span className="section-icon">🏢</span>
            <h2 className="card-title">My organizations</h2>
          </div>
          {orgs.length === 0 ? (
            <div className="org-empty">
              <p>You are not a member of any organization yet.</p>
              <p style={{ marginTop: 6 }}>
                Create one in the Organizations tab.
              </p>
            </div>
          ) : (
            <div className="org-grid">
              {orgs.map((o) => (
                <div className="org-card" key={o.id}>
                  <div className="org-card-icon">🏢</div>
                  <div className="org-card-body">
                    <div className="org-card-name">
                      {o.display_name || o.name}
                    </div>
                    <div className="org-card-meta">
                      <code>{o.name}</code>
                      <span className="org-card-sep">·</span>
                      <code>{o.id}</code>
                    </div>
                  </div>
                  {o.selected_plan ? (
                    <span className="org-member-badge">{o.selected_plan}</span>
                  ) : (
                    <span className="badge badge--neutral">no plan</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
