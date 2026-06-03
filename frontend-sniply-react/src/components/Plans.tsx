import { useEffect, useState } from "react";
import { api, OrgSummary, Plan } from "../api";
import { useTokenGetter } from "../useApi";

// Plan picker: choose an org + a plan; the backend stores it in org metadata
// (object-level check: caller must be a member of the chosen org).
export default function Plans() {
  const getToken = useTokenGetter();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [orgs, setOrgs] = useState<OrgSummary[]>([]);
  const [orgId, setOrgId] = useState("");
  const [msg, setMsg] = useState<{ kind: string; text: string } | null>(null);

  const reload = async () => {
    setPlans(await api.plans(getToken));
    const o = await api.listOrgs(getToken);
    setOrgs(o);
    if (o.length && !orgId) setOrgId(o[0].id);
  };

  useEffect(() => {
    reload().catch((e) => setMsg({ kind: "error", text: e.message }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getToken]);

  const choose = async (planId: string) => {
    if (!orgId) {
      setMsg({ kind: "error", text: "Select an organization first." });
      return;
    }
    try {
      await api.selectPlan(getToken, orgId, planId);
      setMsg({ kind: "success", text: `Plan ${planId} selected.` });
      await reload();
    } catch (e: any) {
      setMsg({ kind: "error", text: e.message });
    }
  };

  const currentPlan = orgs.find((o) => o.id === orgId)?.selected_plan || null;

  return (
    <main className="page-main">
      <header className="page-header">
        <h1 className="page-title">Choose your plan</h1>
        <p className="page-sub">
          Select the organization and the plan that applies to it.
        </p>
      </header>

      {msg && <div className={`alert alert-${msg.kind}`}>{msg.text}</div>}

      {/* ── Organization selector ── */}
      <div className="org-selector-wrap">
        <label className="form-label" htmlFor="orgPicker">
          Organization
        </label>
        {orgs.length === 0 ? (
          <div className="alert alert-error" style={{ maxWidth: 500 }}>
            You are not a member of any organization. Create one in the
            Organization tab first.
          </div>
        ) : (
          <>
            <select
              className="form-input form-select"
              id="orgPicker"
              style={{ maxWidth: 400 }}
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.display_name || o.name}
                  {o.selected_plan ? ` (${o.selected_plan})` : ""}
                </option>
              ))}
            </select>
            <p className="form-hint" style={{ marginTop: 6 }}>
              Plan will be applied to the selected organization.
            </p>
          </>
        )}
      </div>

      {/* ── Plan cards ── */}
      <div className="plans-grid">
        {plans.map((p) => {
          const featured = p.display_name === "Professional";
          const active = currentPlan != null && currentPlan === p.id;
          return (
            <div
              className={`plan-card${featured ? " plan-card--featured" : ""}${
                active ? " plan-card--active" : ""
              }`}
              key={p.id}
            >
              {featured && <div className="featured-badge">Most popular</div>}

              <div className="plan-header">
                <h2 className="plan-name">{p.display_name}</h2>
                <div className="plan-price">{p.price}</div>
                <p className="plan-desc">{p.description}</p>
              </div>

              {active && (
                <div className="plan-check">
                  <span className="check-icon">✓</span> Current plan
                </div>
              )}

              <div className="plan-form">
                <button
                  className={`btn btn-full ${
                    active
                      ? "btn-selected"
                      : featured
                        ? "btn-primary"
                        : "btn-outline"
                  }`}
                  disabled={active}
                  onClick={() => choose(p.id)}
                >
                  {active ? "Current plan" : "Select plan"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </main>
  );
}
