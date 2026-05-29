import { useAuth0 } from "@auth0/auth0-react";

// UpContent landing — content-curation framing with a mock curated-article
// feed. Clearly a DEMO (banner + ribbon are always present).
const MOCK_FEED = [
  {
    title: "The Art of Strategic Spontaneity in Content",
    source: "Marketing Weekly",
    blurb: "How top teams blend planning with in-the-moment curation.",
  },
  {
    title: "5 Curated Feeds Every Brand Should Share",
    source: "ContentOps",
    blurb: "Hand-picked sources that keep your audience coming back.",
  },
  {
    title: "Turning Reads into Shares Across Your Orgs",
    source: "UpContent Labs",
    blurb: "Distribute the right article to the right team, instantly.",
  },
];

export default function Landing() {
  const { loginWithRedirect } = useAuth0();
  return (
    <div>
      <section className="hero">
        <h1>
          Maximize every interaction with{" "}
          <span className="accent">strategic spontaneity</span>
        </h1>
        <p>
          UpContent helps teams discover, curate, and share the content that
          drives engagement — across every brand and organization you manage.
        </p>
        <div style={{ marginTop: 24 }}>
          <button className="btn" onClick={() => loginWithRedirect()}>
            Log in to your workspace
          </button>
        </div>
      </section>
      <div className="container">
        <h2 className="section-title">Your curated feed</h2>
        <p className="muted">
          A preview of articles to share to your organizations (mock data).
        </p>
        <div className="grid cols-3">
          {MOCK_FEED.map((a) => (
            <div className="card" key={a.title}>
              <div className="feed-item">
                <div className="thumb" />
                <div>
                  <h3 style={{ fontSize: 15 }}>{a.title}</h3>
                  <div className="muted" style={{ fontSize: 12 }}>
                    {a.source}
                  </div>
                </div>
              </div>
              <p className="muted" style={{ fontSize: 13 }}>
                {a.blurb}
              </p>
              <button className="btn ghost" disabled>
                Share to org
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
