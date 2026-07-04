import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";
import StatusBadge from "../components/common/StatusBadge.jsx";

function StatCard({ label, value, accent }) {
  return (
    <div className="panel p-5">
      <p className="text-xs text-ink-muted uppercase tracking-wide mono">{label}</p>
      <p className={`text-3xl font-bold mt-2 ${accent}`}>{value}</p>
    </div>
  );
}

export default function DashboardHome() {
  const [summary, setSummary] = useState(null);
  const [runs, setRuns] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.analyticsSummary().then(setSummary).catch((e) => setError(e.message));
    api.listRuns().then((r) => setRuns(r.slice(0, 6))).catch(() => {});
  }, []);

  return (
    <div>
      <Topbar
        title="Overview"
        subtitle="Purple Team exercises across your isolated Ubuntu lab VM"
      />
      <div className="p-8 space-y-8">
        {error && (
          <div className="panel border-red-team/40 p-4 text-red-team text-sm">
            Could not reach the backend: {error}. Is uvicorn running on :8000?
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Runs" value={summary?.total_runs ?? "—"} accent="text-purple-bright" />
          <StatCard label="Total Events" value={summary?.total_events ?? "—"} accent="text-blue-team" />
          <StatCard
            label="Techniques Observed"
            value={summary ? Object.keys(summary.technique_breakdown).length : "—"}
            accent="text-red-team"
          />
          <StatCard
            label="High/Critical Events"
            value={
              summary
                ? (summary.event_severity_breakdown.high || 0) +
                  (summary.event_severity_breakdown.critical || 0)
                : "—"
            }
            accent="text-sev-high"
          />
        </div>

        <div className="panel p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Recent Scenario Runs</h2>
            <Link to="/scenarios" className="text-sm text-purple-bright hover:underline">
              Run a scenario →
            </Link>
          </div>
          {runs.length === 0 ? (
            <p className="text-sm text-ink-muted">
              No runs yet. Head to the Scenario Manager to launch your first training exercise.
            </p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-muted mono text-xs uppercase">
                  <th className="pb-2">Scenario</th>
                  <th className="pb-2">Target</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Events</th>
                  <th className="pb-2">Started</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} className="border-t border-panel-border">
                    <td className="py-2">{r.scenario_name}</td>
                    <td className="py-2 mono text-ink-muted">{r.target_host}</td>
                    <td className="py-2">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-2">{r.event_count}</td>
                    <td className="py-2 text-ink-muted">
                      {new Date(r.started_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {[
            { to: "/timeline", title: "Timeline Viewer", desc: "Chronological view of every captured event." },
            { to: "/attack-graph", title: "Attack Flow Graph", desc: "Interactive node graph of a run's execution chain." },
            { to: "/copilot", title: "AI Security Copilot", desc: "Ask questions about any event or run." },
          ].map((c) => (
            <Link key={c.to} to={c.to} className="panel p-5 hover:border-purple/50 transition-colors">
              <h3 className="font-semibold text-ink">{c.title}</h3>
              <p className="text-sm text-ink-muted mt-1">{c.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
