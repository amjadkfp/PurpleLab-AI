"""
core/mitre_mapper.py
======================
Loads the local MITRE ATT&CK reference data (mitre_data/attack_mappings.json)
and provides lookups used to annotate Events with tactic/technique
information, plus the aggregate view used by the MITRE Mapping dashboard
page.

Mapping strategy
-----------------
Scenario-sourced events already carry a technique ID from
`scenarios/definitions.py` (authored by hand, since we control exactly what
each step does). Log-sourced events are mapped via `classify_line`'s
category from log_collector.py through CATEGORY_TECHNIQUE_MAP below.
"""
import json
from pathlib import Path
from typing import Dict, Optional

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "mitre_data" / "attack_mappings.json"

CATEGORY_TECHNIQUE_MAP: Dict[str, str] = {
    "ssh_failed": "T1110",
    "ssh_accepted": "T1078",
    "useradd": "T1136.001",
    "userdel": "T1136.001",
    "usermod_group": "T1078.003",
    "sudo_command": "T1078.003",
    "cron": "T1053.003",
}


class MitreMapper:
    def __init__(self):
        with open(DATA_PATH, "r") as f:
            self._data: Dict[str, dict] = json.load(f)

    def get_technique(self, technique_id: str) -> Optional[dict]:
        return self._data.get(technique_id)

    def map_log_category(self, category: Optional[str]) -> Optional[dict]:
        if not category:
            return None
        technique_id = CATEGORY_TECHNIQUE_MAP.get(category)
        if not technique_id:
            return None
        info = self.get_technique(technique_id)
        if not info:
            return None
        return {"technique_id": technique_id, **info}

    def all_techniques(self) -> Dict[str, dict]:
        return self._data


_mapper_singleton: Optional[MitreMapper] = None


def get_mitre_mapper() -> MitreMapper:
    global _mapper_singleton
    if _mapper_singleton is None:
        _mapper_singleton = MitreMapper()
    return _mapper_singleton
