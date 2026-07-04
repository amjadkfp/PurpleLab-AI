"""
core/scenario_engine.py
=========================
The orchestrator that ties everything together for a single scenario run:

  1. Opens one guarded SSH session (core/ssh_client.py)
  2. Executes each ScenarioStep's fixed command in order
  3. Records a scenario-sourced Event per step
  4. Collects and parses the scenario's declared log sources
  5. Records log-sourced Events for newly observed lines
  6. Runs MITRE mapping over every event
  7. Runs the AI Copilot over every event to attach explanations
  8. Marks the run complete (or failed) and closes the session

This is intentionally synchronous and sequential - training scenarios are
short (seconds), and the sequential model keeps the resulting timeline
simple to reason about for a learner.
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.ai_copilot import explain_event
from app.core.log_collector import collect_log
from app.core.mitre_mapper import get_mitre_mapper
from app.core.ssh_client import LabSSHClient, SSHCommandNotAllowed, SSHHostNotAllowed
from app.models.event import Event
from app.models.scenario_run import RunStatus, ScenarioRun
from app.scenarios.definitions import ScenarioDefinition, get_scenario

logger = logging.getLogger("purplelab.engine")


class ScenarioNotFound(Exception):
    pass


def run_scenario(db: Session, scenario_key: str) -> ScenarioRun:
    scenario: ScenarioDefinition | None = get_scenario(scenario_key)
    if not scenario:
        raise ScenarioNotFound(f"Unknown scenario: {scenario_key}")

    ssh = LabSSHClient()
    run = ScenarioRun(
        scenario_key=scenario.key,
        scenario_name=scenario.name,
        status=RunStatus.RUNNING,
        target_host=ssh.host,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        ssh.connect()
        _execute_steps(db, run, scenario, ssh)
        _collect_logs(db, run, scenario, ssh)
        run.status = RunStatus.CLEANED_UP if scenario.category == "Cleanup" else RunStatus.COMPLETED
        run.finished_at = datetime.utcnow()
        db.commit()
    except (SSHHostNotAllowed, SSHCommandNotAllowed) as exc:
        logger.error("Guardrail blocked run %s: %s", run.id, exc)
        run.status = RunStatus.FAILED
        run.error_message = str(exc)
        run.finished_at = datetime.utcnow()
        db.commit()
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scenario run %s failed", run.id)
        run.status = RunStatus.FAILED
        run.error_message = str(exc)
        run.finished_at = datetime.utcnow()
        db.commit()
        raise
    finally:
        ssh.close()

    _enrich_events(db, run)
    return run


def _execute_steps(db: Session, run: ScenarioRun, scenario: ScenarioDefinition, ssh: LabSSHClient) -> None:
    for step in scenario.steps:
        result = ssh.run(step.command)
        severity = "low" if step.is_cleanup else ("medium" if step.actor == "attacker_sim" else "info")
        event = Event(
            run_id=run.id,
            timestamp=datetime.utcnow(),
            source="scenario",
            log_source=step.log_source,
            step_key=step.key,
            actor=step.actor,
            action=step.title,
            raw_log=(result.stdout or result.stderr or "").strip()[:4000],
            severity=severity,
            mitre_tactic=step.mitre_tactic if step.mitre_tactic != "N/A" else None,
            mitre_technique_id=step.mitre_technique_id if step.mitre_technique_id != "N/A" else None,
            mitre_technique_name=step.mitre_technique_name if step.mitre_technique_name != "Cleanup" else "Environment Cleanup",
        )
        db.add(event)
        db.commit()


def _collect_logs(db: Session, run: ScenarioRun, scenario: ScenarioDefinition, ssh: LabSSHClient) -> None:
    mapper = get_mitre_mapper()
    for log_source in scenario.log_sources:
        parsed_lines = collect_log(ssh, log_source, tail_lines=100)
        for line in parsed_lines[-25:]:  # cap noise per run
            mapping = mapper.map_log_category(line.category)
            event = Event(
                run_id=run.id,
                timestamp=line.timestamp or datetime.utcnow(),
                source="log",
                log_source=line.log_source,
                actor=line.matched_user,
                action=line.category or "Unclassified log line",
                raw_log=line.raw,
                severity="medium" if line.category else "info",
                mitre_tactic=mapping["tactic"] if mapping else None,
                mitre_technique_id=mapping["technique_id"] if mapping else None,
                mitre_technique_name=mapping["name"] if mapping else None,
            )
            db.add(event)
    db.commit()


def _enrich_events(db: Session, run: ScenarioRun) -> None:
    """Attach AI-generated explanations/detection/mitigation to every event in the run."""
    events = db.query(Event).filter(Event.run_id == run.id).all()
    for event in events:
        try:
            result = explain_event(event)
            event.ai_explanation = result["explanation"]
            event.detection_guidance = result["detection"]
            event.mitigation_guidance = result["mitigation"]
        except Exception:  # noqa: BLE001
            logger.exception("AI enrichment failed for event %s", event.id)
    db.commit()
