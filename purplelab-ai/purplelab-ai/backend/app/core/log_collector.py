"""
core/log_collector.py
=======================
Fetches raw log files from the lab VM (via SSHClient.run, which is itself
allow-listed) and performs light structural parsing so log lines can be
attached to Events for the Log Viewer and Timeline modules.

This module does not interpret *meaning* - that is mitre_mapper.py's and
ai_copilot.py's job. It only turns raw text into normalized rows.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.core.ssh_client import LabSSHClient

# very small set of well-known auth.log / syslog patterns used for
# lightweight classification before MITRE mapping takes over.
PATTERNS = {
    "ssh_failed": re.compile(r"Failed password for (?:invalid user )?(?P<user>\S+)"),
    "ssh_accepted": re.compile(r"Accepted password for (?P<user>\S+)"),
    "useradd": re.compile(r"new user: name=(?P<user>\S+)"),
    "userdel": re.compile(r"delete user '(?P<user>\S+)'"),
    "usermod_group": re.compile(r"add '(?P<user>\S+)' to group '(?P<group>\S+)'"),
    "sudo_command": re.compile(r"sudo:\s+\S+ : .*COMMAND=(?P<command>.+)"),
    "cron": re.compile(r"CRON|crontab", re.IGNORECASE),
}


@dataclass
class ParsedLogLine:
    raw: str
    log_source: str
    category: Optional[str]
    matched_user: Optional[str]
    timestamp: Optional[datetime]


def _try_parse_timestamp(line: str) -> Optional[datetime]:
    # Typical syslog/auth.log prefix: "Jun 12 08:31:02 host process[pid]: ..."
    m = re.match(r"^(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})", line)
    if not m:
        return None
    try:
        parsed = datetime.strptime(m.group("ts"), "%b %d %H:%M:%S")
        return parsed.replace(year=datetime.utcnow().year)
    except ValueError:
        return None


def classify_line(line: str) -> Optional[str]:
    for category, pattern in PATTERNS.items():
        if pattern.search(line):
            return category
    return None


def parse_log_text(raw_text: str, log_source: str) -> List[ParsedLogLine]:
    lines = [l for l in raw_text.splitlines() if l.strip()]
    parsed = []
    for line in lines:
        category = classify_line(line)
        user_match = None
        for pattern in PATTERNS.values():
            m = pattern.search(line)
            if m and "user" in m.groupdict():
                user_match = m.group("user")
                break
        parsed.append(
            ParsedLogLine(
                raw=line,
                log_source=log_source,
                category=category,
                matched_user=user_match,
                timestamp=_try_parse_timestamp(line),
            )
        )
    return parsed


def collect_log(ssh: LabSSHClient, log_source: str, tail_lines: int = 200) -> List[ParsedLogLine]:
    """Fetch the last N lines of a log file from the lab VM and parse them."""
    result = ssh.run(f"sudo -n tail -n {tail_lines} {log_source}")
    if not result.ok:
        return []
    return parse_log_text(result.stdout, log_source)
