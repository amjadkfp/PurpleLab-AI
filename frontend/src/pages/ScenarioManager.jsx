import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";
import StatusBadge from "../components/common/StatusBadge.jsx";

const RISK_COLOR = {
  low: "text-blue-team",
  medium: "text-sev-medium",
  high: "text-sev-high",
};

export default function ScenarioManager() {
  const [scenarios, setScenarios] = useState([]);
  const [running, setRunning] = useState(null);
  const [lastRun, setLastRun] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.listScenarios().then(setScenarios).catch((e) => setError(e.message));
  }, []);

  async function handleRun(key) {
    setRunning(key);
    setError(null);
    setLastRun(null);
    try {
      const run = await api.runScenario(key);
      setLastRun(run);
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(null);
    }
  }

  return (
    <div>
      <Topbar
        title="Scenario Manager"
        subtitle="Predefined, reviewed training scenarios - no arbitrary command execution"
      />
      <div className="p-8 space-y-6">
        {error && (
          <div className="panel border-red-team/40 p-4 text-red-team text-sm">{error}</div>
        )}

        {lastRun && (
          <div className="panel p-5 border-purple/40">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-ink-muted">Run started</p>
                <p className="font-semibold">{lastRun.scenario_name}</p>
              </div>
              <StatusBadge status={lastRun.status} />
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => navigate(`/timeline?run_id=${lastRun.id}`)}
                className="text-sm px-3 py-1.5 rounded-lg bg-purple-dim/40 border border-purple/40 hover:bg-purple-dim/60 transition-colors"
              >
                View Timeline
              </button>
              <button
                onClick={() => navigate(`/attack-graph?run_id=${lastRun.id}`)}
                className="text-sm px-3 py-1.5 rounded-lg bg-panel-raised border border-panel-border hover:border-blue-team/40 transition-colors"
              >
                View Attack Graph
              </button>
              <button
                onClick={() => navigate(`/reports?run_id=${lastRun.id}`)}
                className="text-sm px-3 py-1.5 rounded-lg bg-panel-raised border border-panel-border hover:border-blue-team/40 transition-colors"
              >
                Generate Report
              </button>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-5">
          {scenarios.map((s) => (
            <div key={s.key} className="panel p-5 flex flex-col">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs mono uppercase tracking-wide text-ink-muted">{s.category}</p>
                  <h3 className="font-semibold text-lg mt-1">{s.name}</h3>
                </div>
                <span className={`mono text-xs uppercase ${RISK_COLOR[s.risk_level]}`}>
                  {s.risk_level} risk
                </span>
              </div>
              <p className="text-sm text-ink-muted mt-2 flex-1">{s.description}</p>

              <div className="mt-4 space-y-1.5">
                {s.steps.map((step, i) => (
                  <div key={step.key} className="flex items-center gap-2 text-xs text-ink-muted">
                    <span className="mono text-purple-bright w-4">{i + 1}.</span>
                    <span>{step.title}</span>
                    {step.mitre_technique_id && (
                      <span className="mono text-blue-team ml-auto">{step.mitre_technique_id}</span>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between mt-5">
                {s.has_cleanup ? (
                  <span className="text-[11px] text-blue-team">✓ Includes cleanup step</span>
                ) : (
                  <span className="text-[11px] text-ink-muted">No state changes to clean up</span>
                )}
                <button
                  onClick={() => handleRun(s.key)}
                  disabled={running === s.key}
                  className="text-sm px-4 py-1.5 rounded-lg bg-gradient-to-r from-red-team/80 to-blue-team/80 hover:from-red-team hover:to-blue-team text-void font-medium transition-all disabled:opacity-50"
                >
                  {running === s.key ? "Running…" : "Run Scenario"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
