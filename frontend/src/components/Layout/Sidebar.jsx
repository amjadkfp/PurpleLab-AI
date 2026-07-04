import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: "◈" },
  { to: "/scenarios", label: "Scenario Manager", icon: "▣" },
  { to: "/timeline", label: "Timeline Viewer", icon: "≡" },
  { to: "/attack-graph", label: "Attack Flow Graph", icon: "◇" },
  { to: "/copilot", label: "AI Security Copilot", icon: "✦" },
  { to: "/mitre", label: "MITRE ATT&CK Mapping", icon: "▲" },
  { to: "/logs", label: "Log Viewer", icon: "▤" },
  { to: "/analytics", label: "Analytics", icon: "◐" },
  { to: "/reports", label: "Report Generator", icon: "▦" },
];

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 flex flex-col border-r border-panel-border bg-panel">
      <div className="px-5 py-6 border-b border-panel-border">
        <div className="flex items-baseline gap-1">
          <span className="mono text-lg font-bold text-red-team">Purple</span>
          <span className="mono text-lg font-bold text-blue-team">Lab</span>
          <span className="mono text-lg font-bold text-purple-bright">AI</span>
        </div>
        <p className="text-[11px] text-ink-muted mt-1 tracking-wide">
          Purple Team Training Platform
        </p>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-purple-dim/40 text-ink border border-purple/40"
                  : "text-ink-muted hover:text-ink hover:bg-panel-raised"
              }`
            }
          >
            <span className="mono text-purple-bright w-4 text-center">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-panel-border">
        <div className="text-[10px] text-ink-muted leading-relaxed">
          For use in isolated, authorized lab environments only. All actions
          run against a VM you control.
        </div>
      </div>
    </aside>
  );
}
