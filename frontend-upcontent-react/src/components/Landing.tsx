import { useAuth0 } from "@auth0/auth0-react";

// UpContent landing — editorial hero.
// The preview cards show plan tiers as a teaser. Always a DEMO (banner + ribbon).
const PREVIEW_PLANS = [
  { label: "Starter", price: "$0", per: "/mo", featured: false },
  { label: "Professional", price: "$29", per: "/mo", featured: true },
  { label: "Enterprise", price: "Custom", per: "", featured: false },
];

export default function Landing() {
  const { loginWithRedirect } = useAuth0();
  return (
    <main className="hero">
      <div className="hero-content">
        <span className="eyebrow">Welcome to UpContent</span>
        <h1 className="hero-title">
          UpContent turns content into action
          <br />
          <em>spark a conversation</em>
        </h1>
        <p className="hero-sub">
          Manage your organization, assign roles, and invite your team — all in
          one place.
        </p>
        <button className="btn btn-hero" onClick={() => loginWithRedirect()}>
          Get started →
        </button>
      </div>

      <div className="hero-cards">
        {PREVIEW_PLANS.map((p) => (
          <div
            className={`preview-card${p.featured ? " featured" : ""}`}
            key={p.label}
          >
            <span className="preview-label">{p.label}</span>
            <span className="preview-price">
              {p.price}
              {p.per && <span>{p.per}</span>}
            </span>
          </div>
        ))}
      </div>
    </main>
  );
}
