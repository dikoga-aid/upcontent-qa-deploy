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

  return (
    <div className="container">
      <h2 className="section-title">Portal</h2>
      {error && <div className="notice error">{error}</div>}
      <div className="grid cols-2">
        <div className="card">
          <h3>Profile</h3>
          <div className="row" style={{ marginTop: 8 }}>
            {user?.picture && (
              <img
                src={user.picture}
                alt=""
                width={48}
                height={48}
                style={{ borderRadius: "50%" }}
              />
            )}
            <div>
              <div style={{ fontWeight: 700 }}>{user?.name}</div>
              <div className="muted">{user?.email}</div>
            </div>
          </div>
        </div>
        <div className="card">
          <h3>Token permissions</h3>
          {perms.length === 0 ? (
            <p className="muted">
              No permissions in token. Assign a role to your user in Auth0.
            </p>
          ) : (
            <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
              {perms.map((p) => (
                <code key={p}>{p}</code>
              ))}
            </div>
          )}
        </div>
      </div>

      <h2 className="section-title">Your organizations</h2>
      {orgs.length === 0 ? (
        <p className="muted">
          You are not a member of any organization yet. Create one in the
          Organizations tab.
        </p>
      ) : (
        <div className="grid cols-3">
          {orgs.map((o) => (
            <div className="card" key={o.id}>
              <h3 style={{ fontSize: 16 }}>{o.display_name || o.name}</h3>
              <div className="muted" style={{ fontSize: 12 }}>
                {o.id}
              </div>
              <div style={{ marginTop: 10 }}>
                {o.selected_plan ? (
                  <span className="plan-badge">{o.selected_plan}</span>
                ) : (
                  <span className="tag">no plan</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
