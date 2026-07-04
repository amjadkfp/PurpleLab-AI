"""
models/scenario_run.py
=======================
A ScenarioRun represents a single execution of a predefined training
scenario (e.g. "SSH Brute-Force Simulation") against the lab VM. It is the
parent record that groups all Events produced during that run.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CLEANED_UP = "cleaned_up"


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_key = Column(String, nullable=False, index=True)
    scenario_name = Column(String, nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING, nullable=False)
    target_host = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    events = relationship(
        "Event", back_populates="run", cascade="all, delete-orphan", order_by="Event.timestamp"
    )
