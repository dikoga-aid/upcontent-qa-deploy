import { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { API_BASE_URL } from "../auth-config";

// Sniply landing — editorial hero.
// Teaser cards show the REAL plan catalog from the API. Always a DEMO (banner + ribbon).
interface Plan {
  id: string;
  display_name: string;
  description: string;
  price: string;
}

export default function Landing() {
  const { loginWithRedirect } = useAuth0();
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    // Best-effort fetch of the real catalog. If it fails, render no teaser cards.
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/plans`);
        if (res.ok) {
          setPlans((await res.json()) as Plan[]);
        }
      } catch {
        /* render nothing for the teaser */
      }
    })();
  }, []);

  return (
    <main className="hero">
      <div className="hero-content">
        <span className="eyebrow">Welcome to Sniply</span>
        <h1 className="hero-title">
          Add a call-to-action to every link
          <br />
          <em>convert every share</em>
        </h1>
        <p className="hero-sub">
          Overlay your CTA on any link, track clicks, and manage campaigns
          across every brand and organization you run.
        </p>
        <button className="btn btn-hero" onClick={() => loginWithRedirect()}>
          Get started →
        </button>
      </div>

      <div className="hero-cards">
        {plans.map((p, i) => (
          <div
            className={`preview-card${i === 1 ? " featured" : ""}`}
            key={p.id}
          >
            <span className="preview-label">{p.display_name}</span>
            <span className="preview-price">{p.price}</span>
          </div>
        ))}
      </div>
    </main>
  );
}
