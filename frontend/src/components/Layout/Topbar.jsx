import { useEffect, useState } from "react";
import { api } from "../../api/client.js";

export default function Topbar({ title, subtitle }) {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let mounted = true;
    api
      .health()
      .then(() => mounted && setStatus("online"))
      .catch(() => mounted && setStatus("offline"));
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="flex items-center justify-between px-8 py-5 border-b border-panel-border bg-void/60 backdrop-blur sticky top-0 z-10">
      <div>
        <h1 className="text-xl font-semibold text-ink">{title}</h1>
        {subtitle && <p className="text-sm text-ink-muted mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2 mono text-xs">
        <span
          className={`w-2 h-2 rounded-full ${
            status === "online"
              ? "bg-blue-team shadow-[0_0_8px_2px_rgba(34,211,238,0.6)]"
              : status === "offline"
              ? "bg-red-team shadow-[0_0_8px_2px_rgba(244,63,94,0.6)]"
              : "bg-sev-medium"
          }`}
        />
        <span className="text-ink-muted uppercase tracking-wide">
          Backend {status}
        </span>
      </div>
    </header>
  );
}
