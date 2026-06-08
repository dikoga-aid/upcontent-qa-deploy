import { useAuth0 } from "@auth0/auth0-react";
import { DemoBanner, Nav } from "./components/Chrome";
import Landing from "./components/Landing";
import Portal from "./components/Portal";

// Sniply is a focused authentication demo: login + profile. It authenticates
// against its own API audience (https://sniply-api) with no org scopes, so it
// has no org/plan/role management; that lives in UpContent.
export default function App() {
  const { isAuthenticated, isLoading, error } = useAuth0();

  return (
    <>
      <div className="grid-bg" />
      <div className="demo-ribbon">DEMO</div>
      <DemoBanner />
      <Nav />
      {error && (
        <main className="page-main">
          <div className="alert alert-error">Auth error: {error.message}</div>
        </main>
      )}
      {isLoading ? (
        <main className="page-main">
          <p className="page-sub">Loading…</p>
        </main>
      ) : isAuthenticated ? (
        <Portal />
      ) : (
        <Landing />
      )}
    </>
  );
}
