const COLORS = {
  pending: "text-ink-muted border-panel-border bg-panel-raised",
  running: "text-purple-bright border-purple/40 bg-purple-dim/20 animate-pulse",
  completed: "text-blue-team border-blue-team/40 bg-blue-team/10",
  failed: "text-red-team border-red-team/40 bg-red-team/10",
  cleaned_up: "text-ink-muted border-panel-border bg-panel-raised",
};

export default function StatusBadge({ status }) {
  const cls = COLORS[status] || COLORS.pending;
  return (
    <span className={`mono text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full border ${cls}`}>
      {status}
    </span>
  );
}
