import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { DemoBanner, Nav } from "./components/Chrome";
import Landing from "./components/Landing";
import Portal from "./components/Portal";
import Plans from "./components/Plans";
import Organizations from "./components/Organizations";
import Roles from "./components/Roles";

export default function App() {
  const { isAuthenticated, isLoading, error } = useAuth0();
  const [tab, setTab] = useState("portal");

  return (
    <>
      <div className="grid-bg" />
      <div className="demo-ribbon">DEMO</div>
      <DemoBanner />
      <Nav tab={tab} setTab={setTab} />
      {error && (
        <main className="page-main">
          <div className="alert alert-error">Auth error: {error.message}</div>
        </main>
      )}
      {isLoading ? (
        <main className="page-main">
          <p className="page-sub">Loading…</p>
        </main>
      ) : !isAuthenticated ? (
        <Landing />
      ) : tab === "portal" ? (
        <Portal />
      ) : tab === "plans" ? (
        <Plans />
      ) : tab === "organizations" ? (
        <Organizations />
      ) : (
        <Roles />
      )}
    </>
  );
}
