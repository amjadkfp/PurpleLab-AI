const LABELS = {
  attacker_sim: "Red · Attacker Sim",
  defender: "Blue · Defender",
  system: "System",
};

export default function ActorPill({ actor }) {
  if (!actor) return <span className="text-ink-muted text-xs">—</span>;
  const cls = `actor-${actor}`;
  return <span className={`duality-pill ${cls}`}>{LABELS[actor] || actor}</span>;
}
