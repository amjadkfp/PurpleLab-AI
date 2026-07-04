import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";
import SeverityPill from "../components/common/SeverityPill.jsx";
import ActorPill from "../components/common/ActorPill.jsx";

const RED_ACTORS = ["attacker_sim"];

export default function TimelineViewer() {
  const [params] = useSearchParams();
  const runId = params.get("run_id") || "";
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(runId);
  const [events, setEvents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listRuns().then(setRuns).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    api
      .listEvents({ run_id: selectedRun })
      .then(setEvents)
      .catch((e) => setError(e.message));
  }, [selectedRun]);

  const grouped = useMemo(() => events, [events]);

  return (
    <div>
      <Topbar title="Timeline Viewer" subtitle="Chronological reconstruction of a scenario run" />
      <div className="p-8 space-y-6">
        <div className="flex items-center gap-3">
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
        </div>

        {error && <div className="panel border-red-team/40 p-4 text-red-team text-sm">{error}</div>}

        {!selectedRun && (
          <p className="text-sm text-ink-muted">Select a run above to view its timeline.</p>
        )}

        {selectedRun && grouped.length === 0 && !error && (
          <p className="text-sm text-ink-muted">No events recorded for this run yet.</p>
        )}

        {grouped.length > 0 && (
          <div className="grid grid-cols-[1fr_auto_1fr] gap-0">
            <div />
            <div className="flex flex-col items-center">
              <div className="text-[10px] mono text-red-team mb-2">RED</div>
            </div>
            <div className="flex flex-col items-center">
              <div className="text-[10px] mono text-blue-team mb-2">BLUE / LOG</div>
            </div>
          </div>
        )}

        <div className="relative">
          {grouped.length > 0 && (
            <div className="absolute left-1/2 top-0 bottom-0 duality-spine -translate-x-1/2" />
          )}
          <div className="space-y-6">
            {grouped.map((e) => {
              const isRed = RED_ACTORS.includes(e.actor);
              return (
                <div key={e.id} className="grid grid-cols-[1fr_auto_1fr] gap-4 items-start">
                  <div className={isRed ? "" : "invisible"}>
                    <EventCard event={e} align="right" onClick={() => setSelected(e)} />
                  </div>
                  <div className="flex flex-col items-center pt-2">
                    <div className="w-3 h-3 rounded-full bg-purple border-2 border-void z-10" />
                    <span className="text-[10px] text-ink-muted mono mt-1 whitespace-nowrap">
                      {new Date(e.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className={!isRed ? "" : "invisible"}>
                    <EventCard event={e} align="left" onClick={() => setSelected(e)} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {selected && <EventDrawer event={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function EventCard({ event, align, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`panel p-4 w-full text-left hover:border-purple/50 transition-colors ${
        align === "right" ? "border-r-2 border-r-red-team/50" : "border-l-2 border-l-blue-team/50"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm">{event.action}</span>
        <SeverityPill severity={event.severity} />
      </div>
      <div className="flex items-center gap-2 mt-2">
        <ActorPill actor={event.actor} />
        {event.mitre_technique_id && (
          <span className="mono text-xs text-purple-bright">{event.mitre_technique_id}</span>
        )}
      </div>
    </button>
  );
}

function EventDrawer({ event, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 flex justify-end z-50" onClick={onClose}>
      <div
        className="w-full max-w-md h-full bg-panel border-l border-panel-border p-6 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">{event.action}</h3>
          <button onClick={onClose} className="text-ink-muted hover:text-ink">✕</button>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <ActorPill actor={event.actor} />
          <SeverityPill severity={event.severity} />
        </div>

        {event.mitre_technique_id && (
          <div className="panel p-3 mb-4 border-purple/30">
            <p className="text-xs text-ink-muted mono uppercase">MITRE ATT&CK</p>
            <p className="mono text-purple-bright mt-1">
              {event.mitre_technique_id} — {event.mitre_technique_name}
            </p>
            <p className="text-xs text-ink-muted mt-1">{event.mitre_tactic}</p>
          </div>
        )}

        {event.ai_explanation && (
          <div className="mb-4">
            <p className="text-xs mono text-ink-muted uppercase mb-1">AI Explanation</p>
            <p className="text-sm text-ink">{event.ai_explanation}</p>
          </div>
        )}
        {event.detection_guidance && (
          <div className="mb-4">
            <p className="text-xs mono text-blue-team uppercase mb-1">Detection</p>
            <p className="text-sm text-ink whitespace-pre-line">{event.detection_guidance}</p>
          </div>
        )}
        {event.mitigation_guidance && (
          <div className="mb-4">
            <p className="text-xs mono text-red-team uppercase mb-1">Mitigation</p>
            <p className="text-sm text-ink whitespace-pre-line">{event.mitigation_guidance}</p>
          </div>
        )}

        {event.raw_log && (
          <div>
            <p className="text-xs mono text-ink-muted uppercase mb-1">Raw Log</p>
            <pre className="code text-xs bg-void p-3 rounded-lg border border-panel-border overflow-x-auto whitespace-pre-wrap">
              {event.raw_log}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
