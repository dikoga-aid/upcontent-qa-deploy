import { useAuth0 } from "@auth0/auth0-react";

// DEMO chrome shared by every page: banner + corner ribbon + brand nav.
export function DemoBanner() {
  return (
    <div className="demo-banner">
      DEMO — not a production system; do not enter real credentials.
    </div>
  );
}

export function Nav({
  tab,
  setTab,
}: {
  tab: string;
  setTab: (t: string) => void;
}) {
  const { isAuthenticated, loginWithRedirect, logout, user } = useAuth0();
  const tabs = isAuthenticated
    ? ["portal", "plans", "organizations", "roles"]
    : [];
  return (
    <div className="nav">
      <span className="brand">
        UpContent<span className="dot">.</span>
      </span>
      {tabs.map((t) => (
        <button
          key={t}
          className={"btn ghost"}
          style={{
            textTransform: "capitalize",
            opacity: tab === t ? 1 : 0.7,
            borderColor: tab === t ? "#fff" : undefined,
            color: "#fff",
          }}
          onClick={() => setTab(t)}
        >
          {t}
        </button>
      ))}
      <span className="spacer" />
      {isAuthenticated ? (
        <>
          <span className="muted" style={{ color: "#c7d0e8" }}>
            {user?.name || user?.email}
          </span>
          <button
            onClick={() =>
              logout({ logoutParams: { returnTo: window.location.origin } })
            }
          >
            Log out
          </button>
        </>
      ) : (
        <button onClick={() => loginWithRedirect()}>Log in</button>
      )}
    </div>
  );
}
