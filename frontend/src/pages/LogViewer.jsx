import { useEffect, useState } from "react";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";
import SeverityPill from "../components/common/SeverityPill.jsx";

export default function LogViewer() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [logSource, setLogSource] = useState("");
  const [events, setEvents] = useState([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api.listRuns().then(setRuns).catch(() => {});
  }, []);

  useEffect(() => {
    const params = {};
    if (selectedRun) params.run_id = selectedRun;
    if (logSource) params.log_source = logSource;
    api.listLogEvents(params).then(setEvents).catch(() => {});
  }, [selectedRun, logSource]);

  const filtered = events.filter((e) =>
    query ? e.raw_log?.toLowerCase().includes(query.toLowerCase()) : true
  );

  return (
    <div>
      <Topbar title="Log Viewer" subtitle="Raw, parsed log lines collected from the lab VM" />
      <div className="p-8 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedRun}
            onChange={(e) => setSelectedRun(e.target.value)}
            className="bg-panel-raised border border-panel-border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">All runs</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.scenario_name} — {new Date(r.started_at).toLocaleString()}
              </option>
            ))}
          </select>
          <select
            value={logSource}
            onChange={(e) => setLogSource(e.target.value)}
            className="bg-panel-raised border border-panel-border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">All log sources</option>
            <option value="/var/log/auth.log">/var/log/auth.log</option>
            <option value="/var/log/syslog">/var/log/syslog</option>
          </select>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter raw log text…"
            className="flex-1 min-w-[200px] bg-panel-raised border border-panel-border rounded-lg px-3 py-1.5 text-sm"
          />
        </div>

        <div className="panel overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-panel-raised">
              <tr className="text-left text-ink-muted mono text-xs uppercase">
                <th className="p-3">Time</th>
                <th className="p-3">Source</th>
                <th className="p-3">Category</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Raw Log</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id} className="border-t border-panel-border align-top">
                  <td className="p-3 mono text-xs text-ink-muted whitespace-nowrap">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="p-3 mono text-xs text-blue-team whitespace-nowrap">{e.log_source}</td>
                  <td className="p-3 text-xs">{e.action}</td>
                  <td className="p-3">
                    <SeverityPill severity={e.severity} />
                  </td>
                  <td className="p-3 code text-xs text-ink-muted max-w-xl truncate">{e.raw_log}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center text-ink-muted text-sm">
                    No log events match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
