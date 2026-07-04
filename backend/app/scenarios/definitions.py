"""
scenarios/definitions.py
=========================
This module is the single source of truth for every command PurpleLab AI
is capable of sending to the lab VM. There is no code path anywhere in the
application that builds an SSH command from free-text user input - every
`ScenarioStep.command` below is a fixed string (or a string with a small,
whitelisted, code-controlled substitution like a lab-only username),
authored ahead of time and reviewed like any other source file.

Each scenario models one benign "attacker action -> defender visibility"
pair, mapped to MITRE ATT&CK, so learners can see both sides:
  1. an action is executed on the Ubuntu VM (simulating attacker or
     administrator behavior in a safe lab context)
  2. the resulting log source is fetched and parsed
  3. the event is annotated with a MITRE technique + AI explanation

Every scenario that changes lab-machine state ships a matching `cleanup`
step so the VM can be returned to its baseline.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class ScenarioStep:
    key: str
    title: str
    description: str
    command: str
    actor: str                      # "attacker_sim" | "defender" | "system"
    mitre_tactic: str
    mitre_technique_id: str
    mitre_technique_name: str
    log_source: Optional[str] = None   # remote log file this step should surface in
    is_cleanup: bool = False


@dataclass
class ScenarioDefinition:
    key: str
    name: str
    description: str
    category: str
    risk_level: str                 # "low" | "medium" | "high" (for lab-context sandboxing UX only)
    steps: List[ScenarioStep] = field(default_factory=list)
    log_sources: List[str] = field(default_factory=list)  # log files to collect after the run

    @property
    def has_cleanup(self) -> bool:
        return any(s.is_cleanup for s in self.steps)


LAB_USER = "plab_testuser"
LAB_GROUP = "plab_testgroup"
LAB_FILE = "/tmp/purplelab/sensitive_file.txt"
LAB_DIR = "/tmp/purplelab"


# ---------------------------------------------------------------------------
# 1. SSH Authentication scenario
# ---------------------------------------------------------------------------
SSH_AUTH = ScenarioDefinition(
    key="ssh_auth",
    name="SSH Authentication Activity",
    description=(
        "Simulates a burst of failed SSH login attempts followed by a "
        "successful authentication, mirroring credential-guessing behavior "
        "so learners can see what brute-force activity looks like in "
        "auth.log and how a defender would detect it."
    ),
    category="Initial Access",
    risk_level="low",
    log_sources=["/var/log/auth.log"],
    steps=[
        ScenarioStep(
            key="failed_logins",
            title="Generate failed SSH login attempts",
            description=(
                "Runs 5 loopback SSH attempts against the lab VM's own SSH "
                "service using an intentionally wrong password, generating "
                "the same 'Failed password' entries a brute-force attempt "
                "would leave in auth.log - without touching any other host."
            ),
            command=(
                "echo trying-lab-only-loopback-auth; "
                "for i in 1 2 3 4 5; do "
                "sshpass -p 'intentionally-wrong-pw' ssh -o StrictHostKeyChecking=no "
                "-o PubkeyAuthentication=no -o ConnectTimeout=5 "
                "$(whoami)@127.0.0.1 true 2>/dev/null; done; true"
            ),
            actor="attacker_sim",
            mitre_tactic="Credential Access",
            mitre_technique_id="T1110",
            mitre_technique_name="Brute Force",
            log_source="/var/log/auth.log",
        ),
        ScenarioStep(
            key="successful_login",
            title="Successful authentication",
            description="Confirms the lab account can still authenticate normally after the failed attempts.",
            command="whoami",
            actor="attacker_sim",
            mitre_tactic="Initial Access",
            mitre_technique_id="T1078",
            mitre_technique_name="Valid Accounts",
            log_source="/var/log/auth.log",
        ),
        ScenarioStep(
            key="collect_auth_log",
            title="Collect auth.log for review",
            description="Pulls the relevant auth.log window back for the timeline and MITRE mapping.",
            command="sudo -n tail -n 200 /var/log/auth.log",
            actor="defender",
            mitre_tactic="Detection",
            mitre_technique_id="DS0028",
            mitre_technique_name="Logon Session (Detection Data Source)",
            log_source="/var/log/auth.log",
        ),
    ],
)

# ---------------------------------------------------------------------------
# 2. User & Group Management scenario
# ---------------------------------------------------------------------------
USER_MANAGEMENT = ScenarioDefinition(
    key="user_management",
    name="Local User & Group Manipulation",
    description=(
        "Creates a local group and user account, then elevates its group "
        "membership - modeling how an adversary (or careless admin) "
        "provisions persistence via a new local account."
    ),
    category="Persistence",
    risk_level="medium",
    log_sources=["/var/log/auth.log"],
    steps=[
        ScenarioStep(
            key="create_group",
            title="Create lab test group",
            description=f"Creates group '{LAB_GROUP}' used to scope the test account.",
            command=f"sudo -n groupadd -f {LAB_GROUP}",
            actor="attacker_sim",
            mitre_tactic="Persistence",
            mitre_technique_id="T1136.001",
            mitre_technique_name="Create Account: Local Account",
            log_source="/var/log/auth.log",
        ),
        ScenarioStep(
            key="create_user",
            title="Create lab test user",
            description=f"Creates account '{LAB_USER}' with no login shell (safe, inert account).",
            command=f"sudo -n useradd -m -g {LAB_GROUP} -s /usr/sbin/nologin {LAB_USER}",
            actor="attacker_sim",
            mitre_tactic="Persistence",
            mitre_technique_id="T1136.001",
            mitre_technique_name="Create Account: Local Account",
            log_source="/var/log/auth.log",
        ),
        ScenarioStep(
            key="modify_group_membership",
            title="Modify group membership",
            description=f"Adds '{LAB_USER}' to the 'sudo' group group to mimic privilege-escalation staging.",
            command=f"sudo -n usermod -aG sudo {LAB_USER}",
            actor="attacker_sim",
            mitre_tactic="Privilege Escalation",
            mitre_technique_id="T1078.003",
            mitre_technique_name="Valid Accounts: Local Accounts",
            log_source="/var/log/auth.log",
        ),
        ScenarioStep(
            key="verify_account",
            title="Verify account state",
            description="Confirms the resulting UID/GID and group memberships for the timeline.",
            command=f"id {LAB_USER}",
            actor="defender",
            mitre_tactic="Detection",
            mitre_technique_id="DS0002",
            mitre_technique_name="User Account (Detection Data Source)",
            log_source="/var/log/auth.log",
        ),
    ],
)
USER_MANAGEMENT.steps.append(
    ScenarioStep(
        key="cleanup",
        title="Remove lab test account",
        description="Deletes the test user and group created above.",
        command=f"sudo -n userdel -r {LAB_USER}",
        actor="defender",
        mitre_tactic="N/A",
        mitre_technique_id="N/A",
        mitre_technique_name="Cleanup",
        log_source="/var/log/auth.log",
        is_cleanup=True,
    )
)

# ---------------------------------------------------------------------------
# 3. File Permission Changes scenario
# ---------------------------------------------------------------------------
FILE_PERMISSIONS = ScenarioDefinition(
    key="file_permissions",
    name="File Permission & Ownership Changes",
    description=(
        "Creates a mock sensitive file, then loosens its permissions and "
        "changes ownership - modeling techniques used to stage data for "
        "exfiltration or to weaken access controls."
    ),
    category="Defense Evasion / Collection",
    risk_level="low",
    log_sources=["/var/log/syslog", "/var/log/auth.log"],
    steps=[
        ScenarioStep(
            key="create_target_file",
            title="Create mock sensitive file",
            description=f"Creates a placeholder file at {LAB_FILE} to manipulate.",
            command=f"mkdir -p {LAB_DIR} && echo 'lab-only mock content' | sudo -n tee {LAB_FILE} > /dev/null",
            actor="system",
            mitre_tactic="Collection",
            mitre_technique_id="T1005",
            mitre_technique_name="Data from Local System",
            log_source="/var/log/syslog",
        ),
        ScenarioStep(
            key="weaken_permissions",
            title="Loosen file permissions",
            description=f"Sets world-readable/writable permissions (777) on {LAB_FILE}.",
            command=f"sudo -n chmod 777 {LAB_FILE}",
            actor="attacker_sim",
            mitre_tactic="Defense Evasion",
            mitre_technique_id="T1222.002",
            mitre_technique_name="File and Directory Permissions Modification: Linux/Mac",
            log_source="/var/log/syslog",
        ),
        ScenarioStep(
            key="change_ownership",
            title="Change file ownership",
            description=f"Transfers ownership of {LAB_FILE} to the lab test user context.",
            command=f"sudo -n chown nobody:nogroup {LAB_FILE}",
            actor="attacker_sim",
            mitre_tactic="Defense Evasion",
            mitre_technique_id="T1222.002",
            mitre_technique_name="File and Directory Permissions Modification: Linux/Mac",
            log_source="/var/log/syslog",
        ),
        ScenarioStep(
            key="verify_permissions",
            title="Verify resulting permissions",
            description="Captures the resulting file mode/owner for the timeline.",
            command=f"stat {LAB_FILE}",
            actor="defender",
            mitre_tactic="Detection",
            mitre_technique_id="DS0022",
            mitre_technique_name="File (Detection Data Source)",
            log_source="/var/log/syslog",
        ),
    ],
)
FILE_PERMISSIONS.steps.append(
    ScenarioStep(
        key="cleanup",
        title="Remove mock file",
        description=f"Deletes {LAB_DIR} and its contents.",
        command=f"sudo -n rm -rf {LAB_DIR}",
        actor="defender",
        mitre_tactic="N/A",
        mitre_technique_id="N/A",
        mitre_technique_name="Cleanup",
        log_source="/var/log/syslog",
        is_cleanup=True,
    )
)

# ---------------------------------------------------------------------------
# 4. Scheduled Tasks scenario
# ---------------------------------------------------------------------------
SCHEDULED_TASKS = ScenarioDefinition(
    key="scheduled_tasks",
    name="Scheduled Task Persistence",
    description=(
        "Installs a benign cron job for the lab user, modeling how "
        "adversaries establish persistence via scheduled tasks."
    ),
    category="Persistence",
    risk_level="medium",
    log_sources=["/var/log/syslog"],
    steps=[
        ScenarioStep(
            key="install_cron",
            title="Install lab cron job",
            description="Adds a harmless cron entry (writes a timestamp to a lab-only file every minute).",
            command=(
                f"( sudo -n crontab -l 2>/dev/null; "
                f"echo '* * * * * echo purplelab-heartbeat >> {LAB_DIR}/cron_heartbeat.log' ) "
                f"| sudo -n crontab -"
            ),
            actor="attacker_sim",
            mitre_tactic="Persistence",
            mitre_technique_id="T1053.003",
            mitre_technique_name="Scheduled Task/Job: Cron",
            log_source="/var/log/syslog",
        ),
        ScenarioStep(
            key="verify_cron",
            title="Verify cron installation",
            description="Lists the current crontab to confirm the entry was installed.",
            command="sudo -n crontab -l",
            actor="defender",
            mitre_tactic="Detection",
            mitre_technique_id="DS0003",
            mitre_technique_name="Scheduled Job (Detection Data Source)",
            log_source="/var/log/syslog",
        ),
    ],
)
SCHEDULED_TASKS.steps.append(
    ScenarioStep(
        key="cleanup",
        title="Remove lab cron job",
        description="Clears the crontab installed by this scenario.",
        command="sudo -n crontab -r",
        actor="defender",
        mitre_tactic="N/A",
        mitre_technique_id="N/A",
        mitre_technique_name="Cleanup",
        log_source="/var/log/syslog",
        is_cleanup=True,
    )
)

# ---------------------------------------------------------------------------
# 5. Full Environment Cleanup scenario (standalone, idempotent)
# ---------------------------------------------------------------------------
FULL_CLEANUP = ScenarioDefinition(
    key="full_cleanup",
    name="Full Lab Environment Cleanup",
    description=(
        "Runs every individual cleanup step across all scenarios in one "
        "pass so the VM is guaranteed to return to baseline, even if a "
        "prior run failed partway through."
    ),
    category="Cleanup",
    risk_level="low",
    log_sources=[],
    steps=[
        ScenarioStep(
            key="cleanup_user",
            title="Remove lab test account (idempotent)",
            description="Deletes the lab test user/group if present.",
            command=f"sudo -n userdel -r {LAB_USER}",
            actor="defender", mitre_tactic="N/A", mitre_technique_id="N/A",
            mitre_technique_name="Cleanup", is_cleanup=True,
        ),
        ScenarioStep(
            key="cleanup_files",
            title="Remove lab working directory",
            description=f"Deletes {LAB_DIR} recursively if present.",
            command=f"sudo -n rm -rf {LAB_DIR}",
            actor="defender", mitre_tactic="N/A", mitre_technique_id="N/A",
            mitre_technique_name="Cleanup", is_cleanup=True,
        ),
        ScenarioStep(
            key="cleanup_cron",
            title="Clear crontab",
            description="Removes any crontab installed by the scheduled tasks scenario.",
            command="sudo -n crontab -r",
            actor="defender", mitre_tactic="N/A", mitre_technique_id="N/A",
            mitre_technique_name="Cleanup", is_cleanup=True,
        ),
    ],
)


SCENARIOS: List[ScenarioDefinition] = [
    SSH_AUTH,
    USER_MANAGEMENT,
    FILE_PERMISSIONS,
    SCHEDULED_TASKS,
    FULL_CLEANUP,
]

SCENARIOS_BY_KEY = {s.key: s for s in SCENARIOS}


def get_scenario(key: str) -> Optional[ScenarioDefinition]:
    return SCENARIOS_BY_KEY.get(key)
