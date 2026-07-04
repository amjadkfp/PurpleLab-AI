import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";

export default function Reports() {
  const [params] = useSearchParams();
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(params.get("run_id") || "");
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listRuns().then(setRuns).catch(() => {});
    refreshReports();
  }, []);

  function refreshReports() {
    api.listReports().then(setReports).catch(() => {});
  }

  async function generate(format) {
    if (!selectedRun) {
      setError("Select a scenario run first.");
      return;
    }
    setGenerating(format);
    setError(null);
    try {
      await api.generateReport(selectedRun, format);
      refreshReports();
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(null);
    }
  }

  return (
    <div>
      <Topbar
        title="Report Generator"
        subtitle="Export a scenario run as a shareable HTML or PDF incident-style report"
      />
      <div className="p-8 space-y-6">
        <div className="panel p-6">
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm text-ink-muted">Run:</label>
            <select
              value={selectedRun}
              onChange={(e) => setSelectedRun(e.target.value)}
              className="bg-panel-raised border border-panel-border rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="">Select a run…</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.scenario_name} — {new Date(r.started_at).toLocaleString()}
                </option>
              ))}
            </select>
            <button
              onClick={() => generate("html")}
              disabled={generating === "html"}
              className="px-4 py-1.5 rounded-lg bg-purple-dim/40 border border-purple/40 hover:bg-purple-dim/60 text-sm disabled:opacity-50"
            >
              {generating === "html" ? "Generating…" : "Generate HTML Report"}
            </button>
            <button
              onClick={() => generate("pdf")}
              disabled={generating === "pdf"}
              className="px-4 py-1.5 rounded-lg bg-panel-raised border border-panel-border hover:border-blue-team/40 text-sm disabled:opacity-50"
            >
              {generating === "pdf" ? "Generating…" : "Generate PDF Report"}
            </button>
          </div>
          {error && <p className="text-red-team text-sm mt-3">{error}</p>}
          <p className="text-xs text-ink-muted mt-3">
            PDF export requires WeasyPrint's system libraries (pango, cairo, gdk-pixbuf) - see the
            README. HTML export always works.
          </p>
        </div>

        <div className="panel p-6">
          <h3 className="font-semibold mb-4">Generated Reports</h3>
          {reports.length === 0 ? (
            <p className="text-sm text-ink-muted">No reports generated yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-ink-muted mono text-xs uppercase">
                  <th className="pb-2">Format</th>
                  <th className="pb-2">Created</th>
                  <th className="pb-2">Download</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id} className="border-t border-panel-border">
                    <td className="py-2 uppercase mono text-xs">{r.format}</td>
                    <td className="py-2 text-ink-muted">{new Date(r.created_at).toLocaleString()}</td>
                    <td className="py-2">
                      <a
                        href={r.download_url}
                        className="text-purple-bright hover:underline"
                        target="_blank"
                        rel="noreferrer"
                      >
                        Download →
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
