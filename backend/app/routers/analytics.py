"""
routers/analytics.py
=======================
Aggregate statistics for the Analytics Dashboard module's Chart.js
visualizations: runs over time, severity distribution, technique
frequency, and per-category tactic coverage.
"""
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.scenario_run import RunStatus, ScenarioRun

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    runs = db.query(ScenarioRun).all()
    events = db.query(Event).all()

    status_counts = Counter(r.status.value if hasattr(r.status, "value") else r.status for r in runs)
    severity_counts = Counter(e.severity for e in events)

    tactic_counts: dict[str, int] = defaultdict(int)
    technique_counts: dict[str, int] = defaultdict(int)
    for e in events:
        if e.mitre_tactic:
            tactic_counts[e.mitre_tactic] += 1
        if e.mitre_technique_id:
            technique_counts[e.mitre_technique_id] += 1

    scenario_counts = Counter(r.scenario_name for r in runs)

    return {
        "total_runs": len(runs),
        "total_events": len(events),
        "run_status_breakdown": status_counts,
        "event_severity_breakdown": severity_counts,
        "tactic_breakdown": dict(tactic_counts),
        "technique_breakdown": dict(technique_counts),
        "runs_by_scenario": dict(scenario_counts),
    }
