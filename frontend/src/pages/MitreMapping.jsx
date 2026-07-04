import { useEffect, useState } from "react";
import Topbar from "../components/Layout/Topbar.jsx";
import { api } from "../api/client.js";

export default function MitreMapping() {
  const [techniques, setTechniques] = useState({});
  const [observed, setObserved] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.listTechniques().then(setTechniques).catch(() => {});
    api.observedTechniques().then(setObserved).catch(() => {});
  }, []);

  const observedIds = new Set(observed.map((o) => o.technique_id));
  const maxCount = Math.max(1, ...observed.map((o) => o.count));

  return (
    <div>
      <Topbar
        title="MITRE ATT&CK Mapping"
        subtitle="Reference techniques used across PurpleLab AI, with observation frequency from your runs"
      />
      <div className="p-8 grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 grid sm:grid-cols-2 gap-4">
          {Object.entries(techniques).map(([id, t]) => {
            const obs = observed.find((o) => o.technique_id === id);
            const intensity = obs ? obs.count / maxCount : 0;
            return (
              <button
                key={id}
                onClick={() => setSelected({ id, ...t, count: obs?.count || 0 })}
                className="panel p-4 text-left hover:border-purple/50 transition-colors relative overflow-hidden"
              >
                {observedIds.has(id) && (
                  <div
                    className="absolute inset-0 bg-purple pointer-events-none"
                    style={{ opacity: 0.08 + intensity * 0.25 }}
                  />
                )}
                <div className="relative">
                  <div className="flex items-center justify-between">
                    <span className="mono text-blue-team text-sm">{id}</span>
                    {obs && (
                      <span className="mono text-[10px] text-purple-bright bg-purple-dim/40 px-2 py-0.5 rounded-full">
                        seen ×{obs.count}
                      </span>
                    )}
                  </div>
                  <p className="font-medium text-sm mt-1">{t.name}</p>
                  <p className="text-xs text-ink-muted mt-1">{t.tactic}</p>
                </div>
              </button>
            );
          })}
        </div>

        <div className="panel p-5 h-fit sticky top-24">
          {!selected ? (
            <p className="text-sm text-ink-muted">
              Select a technique to see its description, detection guidance, and mitigation
              recommendations.
            </p>
          ) : (
            <div>
              <div className="flex items-center justify-between">
                <span className="mono text-blue-team">{selected.id}</span>
                {selected.count > 0 && (
                  <span className="text-xs text-purple-bright">Observed {selected.count}×</span>
                )}
              </div>
              <h3 className="font-semibold text-lg mt-2">{selected.name}</h3>
              <p className="text-xs text-ink-muted mt-1">{selected.tactic}</p>
              <p className="text-sm text-ink mt-4">{selected.description}</p>

              <div className="mt-4">
                <p className="text-xs mono text-blue-team uppercase mb-1">Detection</p>
                <p className="text-sm text-ink-muted">{selected.detection}</p>
              </div>
              <div className="mt-4">
                <p className="text-xs mono text-red-team uppercase mb-1">Mitigation</p>
                <p className="text-sm text-ink-muted">{selected.mitigation}</p>
              </div>
              {selected.url && (
                <a
                  href={selected.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block mt-4 text-sm text-purple-bright hover:underline"
                >
                  View on attack.mitre.org →
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
