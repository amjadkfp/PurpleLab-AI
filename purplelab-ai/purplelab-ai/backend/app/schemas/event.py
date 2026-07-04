"""
schemas/event.py
=================
Contracts for events, the timeline view, and the React-Flow attack graph.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EventOut(BaseModel):
    id: str
    run_id: str
    timestamp: datetime
    source: str
    log_source: Optional[str] = None
    step_key: Optional[str] = None
    actor: Optional[str] = None
    action: str
    raw_log: Optional[str] = None
    severity: str
    mitre_tactic: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    ai_explanation: Optional[str] = None
    detection_guidance: Optional[str] = None
    mitigation_guidance: Optional[str] = None

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: str
    type: str = "default"
    data: dict
    position: dict


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False


class AttackGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class CopilotAskRequest(BaseModel):
    question: str
    run_id: Optional[str] = None
    event_id: Optional[str] = None


class CopilotAskResponse(BaseModel):
    answer: str
