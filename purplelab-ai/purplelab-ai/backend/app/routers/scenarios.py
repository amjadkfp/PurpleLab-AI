"""
routers/scenarios.py
======================
Scenario Manager endpoints: list available predefined scenarios, launch a
run, check its status, and list past runs.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.scenario_engine import ScenarioNotFound, run_scenario
from app.core.ssh_client import SSHCommandNotAllowed, SSHHostNotAllowed
from app.database import get_db
from app.models.event import Event
from app.models.scenario_run import ScenarioRun
from app.scenarios.definitions import SCENARIOS
from app.schemas.scenario import (
    ScenarioInfo,
    ScenarioRunDetail,
    ScenarioRunOut,
    ScenarioRunRequest,
    ScenarioStepInfo,
)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioInfo])
def list_scenarios():
    """Return every predefined scenario definition available to run."""
    return [
        ScenarioInfo(
            key=s.key,
            name=s.name,
            description=s.description,
            category=s.category,
            risk_level=s.risk_level,
            has_cleanup=s.has_cleanup,
            steps=[
                ScenarioStepInfo(
                    key=st.key, title=st.title, description=st.description,
                    mitre_technique_id=None if st.mitre_technique_id == "N/A" else st.mitre_technique_id,
                )
                for st in s.steps
            ],
        )
        for s in SCENARIOS
    ]


@router.post("/run", response_model=ScenarioRunOut)
def run_scenario_endpoint(payload: ScenarioRunRequest, db: Session = Depends(get_db)):
    """
    Synchronously execute a predefined scenario against the configured lab
    VM and return the resulting run record. Kept synchronous (rather than a
    background task) so the UI can immediately show full results - lab
    scenarios complete in a few seconds.
    """
    try:
        run = run_scenario(db, payload.scenario_key)
        return run
    except ScenarioNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (SSHHostNotAllowed, SSHCommandNotAllowed) as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {exc}")


@router.get("/runs", response_model=list[ScenarioRunDetail])
def list_runs(db: Session = Depends(get_db)):
    runs = db.query(ScenarioRun).order_by(ScenarioRun.started_at.desc()).limit(100).all()
    out = []
    for r in runs:
        count = db.query(Event).filter(Event.run_id == r.id).count()
        out.append(ScenarioRunDetail(**ScenarioRunOut.model_validate(r).model_dump(), event_count=count))
    return out


@router.get("/runs/{run_id}", response_model=ScenarioRunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    r = db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    count = db.query(Event).filter(Event.run_id == r.id).count()
    return ScenarioRunDetail(**ScenarioRunOut.model_validate(r).model_dump(), event_count=count)
