"""
routers/events.py
===================
Backs three dashboard modules from one data source (Event rows):
  - Timeline Viewer:      GET /api/events?run_id=...
  - Log Viewer:           GET /api/events/logs?run_id=...
  - Attack Flow Graph:    GET /api/events/graph/{run_id}
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.scenario_run import ScenarioRun
from app.schemas.event import AttackGraph, EventOut, GraphEdge, GraphNode

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(
    run_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Chronological event list for the Timeline Viewer, with optional filters."""
    q = db.query(Event)
    if run_id:
        q = q.filter(Event.run_id == run_id)
    if severity:
        q = q.filter(Event.severity == severity)
    if source:
        q = q.filter(Event.source == source)
    return q.order_by(Event.timestamp).all()


@router.get("/logs", response_model=list[EventOut])
def list_log_events(
    run_id: str | None = Query(default=None),
    log_source: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Raw log-derived events for the Log Viewer module."""
    q = db.query(Event).filter(Event.source == "log")
    if run_id:
        q = q.filter(Event.run_id == run_id)
    if log_source:
        q = q.filter(Event.log_source == log_source)
    return q.order_by(Event.timestamp).all()


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


SEVERITY_COLOR = {
    "critical": "#f87171",
    "high": "#fb923c",
    "medium": "#facc15",
    "low": "#a3a3a3",
    "info": "#7c7c8a",
}


@router.get("/graph/{run_id}", response_model=AttackGraph)
def get_attack_graph(run_id: str, db: Session = Depends(get_db)):
    """
    Builds a React-Flow compatible node/edge graph for the Attack Flow
    Graph module: one node per scenario-sourced step, chained in execution
    order, colored by severity and labeled with its MITRE technique.
    """
    run = db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = (
        db.query(Event)
        .filter(Event.run_id == run_id, Event.source == "scenario")
        .order_by(Event.timestamp)
        .all()
    )

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for idx, event in enumerate(events):
        node_id = event.id
        label = event.action
        subtitle = f"{event.mitre_technique_id} - {event.mitre_technique_name}" if event.mitre_technique_id else "No MITRE mapping"
        nodes.append(
            GraphNode(
                id=node_id,
                data={
                    "label": label,
                    "subtitle": subtitle,
                    "actor": event.actor,
                    "severity": event.severity,
                    "color": SEVERITY_COLOR.get(event.severity, "#7c7c8a"),
                },
                position={"x": 0, "y": idx * 140},
            )
        )
        if idx > 0:
            prev = events[idx - 1]
            edges.append(
                GraphEdge(
                    id=f"e-{prev.id}-{event.id}",
                    source=prev.id,
                    target=event.id,
                    label=event.mitre_tactic or "",
                    animated=event.severity in ("medium", "high", "critical"),
                )
            )

    return AttackGraph(nodes=nodes, edges=edges)
