"""
routers/mitre.py
==================
Serves the local MITRE ATT&CK reference dataset plus an aggregate view of
which techniques have actually been observed across runs, for the MITRE
Mapping dashboard module.
"""
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.mitre_mapper import get_mitre_mapper
from app.database import get_db
from app.models.event import Event

router = APIRouter(prefix="/api/mitre", tags=["mitre"])


@router.get("/techniques")
def list_techniques():
    """Full local MITRE ATT&CK reference data used throughout the app."""
    return get_mitre_mapper().all_techniques()


@router.get("/observed")
def observed_techniques(db: Session = Depends(get_db)):
    """
    Counts how many times each MITRE technique has actually appeared in
    captured events, joined with reference metadata - powers the heatmap-
    style summary in the MITRE Mapping page.
    """
    mapper = get_mitre_mapper()
    rows = (
        db.query(Event.mitre_technique_id)
        .filter(Event.mitre_technique_id.isnot(None))
        .all()
    )
    counts = Counter(r[0] for r in rows)
    result = []
    for technique_id, count in counts.most_common():
        info = mapper.get_technique(technique_id) or {}
        result.append({"technique_id": technique_id, "count": count, **info})
    return result
