const COLORS = {
  critical: "text-sev-critical border-sev-critical/40 bg-sev-critical/10",
  high: "text-sev-high border-sev-high/40 bg-sev-high/10",
  medium: "text-sev-medium border-sev-medium/40 bg-sev-medium/10",
  low: "text-sev-low border-sev-low/40 bg-sev-low/10",
  info: "text-sev-info border-sev-info/40 bg-sev-info/10",
};

export default function SeverityPill({ severity = "info" }) {
  const cls = COLORS[severity] || COLORS.info;
  return (
    <span className={`mono text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full border ${cls}`}>
      {severity}
    </span>
  );
}
