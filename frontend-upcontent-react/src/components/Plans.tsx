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

  return (
    <div className="container">
      <h2 className="section-title">Choose a plan</h2>
      {msg && <div className={`notice ${msg.kind}`}>{msg.text}</div>}
      <label>Organization</label>
      <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
        {orgs.length === 0 && <option value="">No organizations yet</option>}
        {orgs.map((o) => (
          <option key={o.id} value={o.id}>
            {o.display_name || o.name} {o.selected_plan ? `(${o.selected_plan})` : ""}
          </option>
        ))}
      </select>
      <div className="grid cols-3" style={{ marginTop: 18 }}>
        {plans.map((p) => (
          <div className="card" key={p.id}>
            <h3>{p.display_name}</h3>
            <div style={{ fontSize: 24, fontWeight: 800 }}>{p.price}</div>
            <p className="muted">{p.description}</p>
            <button className="btn" onClick={() => choose(p.id)}>
              Select {p.display_name}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
