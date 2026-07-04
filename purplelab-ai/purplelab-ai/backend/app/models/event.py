"""
models/event.py
================
An Event is a single, atomic, timestamped occurrence captured either:
  - directly from a scenario step being executed (source="scenario"), or
  - parsed out of collected Ubuntu VM logs (source="log")

Each event can optionally carry a MITRE ATT&CK mapping and an AI-generated
explanation, which are populated asynchronously by mitre_mapper.py and
ai_copilot.py respectively.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("scenario_runs.id"), nullable=False, index=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, nullable=False)          # "scenario" | "log"
    log_source = Column(String, nullable=True)        # e.g. auth.log, syslog, audit.log
    step_key = Column(String, nullable=True)          # scenario step this event belongs to
    actor = Column(String, nullable=True)              # e.g. attacker, defender, system
    action = Column(String, nullable=False)            # short human label, e.g. "Failed SSH login"
    raw_log = Column(Text, nullable=True)               # original captured log line(s)
    severity = Column(String, default="info")          # info | low | medium | high | critical

    # MITRE ATT&CK mapping
    mitre_tactic = Column(String, nullable=True)
    mitre_technique_id = Column(String, nullable=True)
    mitre_technique_name = Column(String, nullable=True)

    # AI Copilot output
    ai_explanation = Column(Text, nullable=True)
    detection_guidance = Column(Text, nullable=True)
    mitigation_guidance = Column(Text, nullable=True)

    run = relationship("ScenarioRun", back_populates="events")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "log_source": self.log_source,
            "step_key": self.step_key,
            "actor": self.actor,
            "action": self.action,
            "raw_log": self.raw_log,
            "severity": self.severity,
            "mitre_tactic": self.mitre_tactic,
            "mitre_technique_id": self.mitre_technique_id,
            "mitre_technique_name": self.mitre_technique_name,
            "ai_explanation": self.ai_explanation,
            "detection_guidance": self.detection_guidance,
            "mitigation_guidance": self.mitigation_guidance,
        }
