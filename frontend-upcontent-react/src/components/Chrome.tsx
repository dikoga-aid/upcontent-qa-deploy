import { useAuth0 } from "@auth0/auth0-react";

// DEMO chrome shared by every page: banner + corner ribbon + brand nav.
export function DemoBanner() {
  return (
    <div className="demo-banner">
      DEMO — not a production system; do not enter real credentials.
    </div>
  );
}

const NAV_TABS: { id: string; label: string }[] = [
  { id: "portal", label: "Profile" },
  { id: "plans", label: "Plans" },
  { id: "organizations", label: "Organization" },
  { id: "roles", label: "Roles" },
];

export function Nav({
  tab,
  setTab,
}: {
  tab: string;
  setTab: (t: string) => void;
}) {
  const { isAuthenticated, loginWithRedirect, logout, user } = useAuth0();
  return (
    <nav className="nav">
      <div className="nav-inner">
        <span className="logo">
          <img className="logo-img" src="/logo.svg" alt="UpContent" />
        </span>
        {isAuthenticated && (
          <div className="nav-links">
            {NAV_TABS.map((t) => (
              <button
                key={t.id}
                className={`nav-link${tab === t.id ? " active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
        )}
        <div className="nav-user">
          {isAuthenticated ? (
            <>
              <span className="nav-username">{user?.name || user?.email}</span>
              <button
                className="btn btn-ghost"
                onClick={() =>
                  logout({ logoutParams: { returnTo: window.location.origin } })
                }
              >
                Sign out
              </button>
            </>
          ) : (
            <button className="btn btn-primary" onClick={() => loginWithRedirect()}>
              Sign in
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
