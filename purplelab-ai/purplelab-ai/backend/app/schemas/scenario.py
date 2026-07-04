"""
schemas/scenario.py
====================
Request/response contracts for the Scenario Manager module.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ScenarioStepInfo(BaseModel):
    key: str
    title: str
    description: str
    mitre_technique_id: Optional[str] = None


class ScenarioInfo(BaseModel):
    """Metadata describing a predefined scenario definition."""
    key: str
    name: str
    description: str
    category: str
    risk_level: str
    steps: List[ScenarioStepInfo]
    has_cleanup: bool


class ScenarioRunRequest(BaseModel):
    scenario_key: str


class ScenarioRunOut(BaseModel):
    id: str
    scenario_key: str
    scenario_name: str
    status: str
    target_host: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ScenarioRunDetail(ScenarioRunOut):
    event_count: int
