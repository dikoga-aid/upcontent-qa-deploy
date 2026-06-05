import { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { api, Me } from "../api";
import { useTokenGetter } from "../useApi";

// Portal: profile + the org context the access token carries (org / role / plan,
// stamped by the post-login action). Sniply has no org scopes, so it reads this
// straight from the token via /api/me (no Management API call). Org/plan/role
// *management* lives in UpContent.
export default function Portal() {
  const { user } = useAuth0();
  const getToken = useTokenGetter();
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setMe(await api.me(getToken));
      } catch (e: any) {
        setError(e.message || "Failed to load profile.");
      }
    })();
  }, [getToken]);

  const name = user?.name || user?.email || "Unknown user";
  const initial = (name || "?").substring(0, 1).toUpperCase();
  const inOrg = Boolean(me?.org_id);

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
            {me?.org_name && (
              <span className="meta-pill meta-pill--org">
                <span className="meta-icon">🏢</span>
                <span>{me.org_name}</span>
              </span>
            )}
            {me?.plan ? (
              <span className="meta-pill meta-pill--plan">
                <span className="meta-icon">★</span>
                <span>{me.plan}</span>
              </span>
            ) : (
              inOrg && (
                <span className="meta-pill meta-pill--warn">
                  <span className="meta-icon">!</span> No plan selected
                </span>
              )
            )}
          </div>
        </div>
      </div>

      {/* ── Detail grid ── */}
      <div className="portal-grid">
        {/* Identity */}
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
          {!me || me.permissions.length === 0 ? (
            <p className="card-sub">No permissions in token.</p>
          ) : (
            <div className="tag-cloud">
              {me.permissions.map((p) => (
                <span className="tag" key={p}>
                  {p}
                </span>
              ))}
            </div>
          )}
        </section>

        {/* Organization context (from the access token, not the Management API) */}
        <section className="card portal-section portal-section--wide">
          <div className="section-header">
            <span className="section-icon">🏢</span>
            <h2 className="card-title">Organization context</h2>
          </div>
          {!inOrg ? (
            <div className="org-empty">
              <p>You are not signed in within an organization context.</p>
              <p style={{ marginTop: 6 }}>
                Organization, role, and plan management live in UpContent.
              </p>
            </div>
          ) : (
            <dl className="info-list">
              <div className="info-row">
                <dt>Organization</dt>
                <dd>{me?.org_name || <code>{me?.org_id}</code>}</dd>
              </div>
              <div className="info-row">
                <dt>Organization ID</dt>
                <dd>
                  <code>{me?.org_id}</code>
                </dd>
              </div>
              <div className="info-row">
                <dt>Roles</dt>
                <dd>
                  {me?.roles && me.roles.length > 0 ? (
                    <div className="tag-cloud">
                      {me.roles.map((r) => (
                        <span className="tag" key={r}>
                          {r}
                        </span>
                      ))}
                    </div>
                  ) : (
                    "—"
                  )}
                </dd>
              </div>
              <div className="info-row">
                <dt>Plan</dt>
                <dd>
                  {me?.plan ? (
                    <span className="org-member-badge">{me.plan}</span>
                  ) : (
                    <span className="badge badge--neutral">no plan</span>
                  )}
                </dd>
              </div>
            </dl>
          )}
        </section>
      </div>
    </main>
  );
}
