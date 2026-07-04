"""
routers/copilot.py
=====================
Backs the AI Security Copilot chat panel. Accepts a free-form learner
question, optionally scoped to a run/event for context, and returns an
AI-generated (or rule-based fallback) answer.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.ai_copilot import ask_copilot
from app.database import get_db
from app.models.event import Event
from app.models.scenario_run import ScenarioRun
from app.schemas.event import CopilotAskRequest, CopilotAskResponse

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("/ask", response_model=CopilotAskResponse)
def ask(payload: CopilotAskRequest, db: Session = Depends(get_db)):
    context = ""
    if payload.event_id:
        event = db.query(Event).filter(Event.id == payload.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        context = (
            f"Event: {event.action} | Actor: {event.actor} | "
            f"MITRE: {event.mitre_technique_id} {event.mitre_technique_name} | "
            f"Raw log: {event.raw_log}"
        )
    elif payload.run_id:
        run = db.query(ScenarioRun).filter(ScenarioRun.id == payload.run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        events = db.query(Event).filter(Event.run_id == run.id).order_by(Event.timestamp).all()
        summary = "; ".join(f"{e.action} ({e.mitre_technique_id or 'unmapped'})" for e in events)
        context = f"Scenario: {run.scenario_name} | Events: {summary}"

    answer = ask_copilot(payload.question, context)
    return CopilotAskResponse(answer=answer)
