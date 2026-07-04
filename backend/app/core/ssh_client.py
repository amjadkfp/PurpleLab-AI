"""
core/ssh_client.py
===================
Thin, safety-conscious wrapper around Paramiko for talking to the Ubuntu
lab VM from Kali.

Design intent (read before modifying)
--------------------------------------
This client is deliberately narrow. It exposes:
  - `connect()` / `close()` for session lifecycle
  - `run(command)` which only accepts commands from a fixed allow-list
    built from the predefined scenario step definitions (see
    app/scenarios/definitions.py)
  - `fetch_file(remote_path)` for pulling log files back for parsing

It intentionally does NOT expose a generic "run any command" method to
routers or the frontend. Arbitrary remote command execution from user input
is out of scope for this project by design - every command that can reach
the lab VM is defined in code, reviewed, and shipped as part of a scenario
definition, never constructed from free-text user input.

Safety guardrails
------------------
1. `settings.allowed_lab_hosts_list` is a hard allow-list. connect() raises
   if the configured target host is not on it.
2. Commands are matched against `ALLOWED_COMMAND_PREFIXES` before being
   sent - this is a defense-in-depth check on top of (1), in case a future
   scenario definition is edited carelessly.
"""
import io
import logging
from typing import Optional

import paramiko

from app.config import get_settings

logger = logging.getLogger("purplelab.ssh")

# Defense-in-depth allow-list: every scenario-issued command must start with
# one of these. This keeps the SSH layer safe even if a scenario definition
# is modified without care. Extend this list only when adding a new,
# reviewed scenario.
ALLOWED_COMMAND_PREFIXES = [
    "sudo -n cat /var/log",
    "sudo -n tail",
    "sudo -n journalctl",
    "cat /var/log",
    "tail",
    "journalctl",
    "sudo -n useradd",
    "sudo -n userdel",
    "sudo -n usermod",
    "sudo -n groupadd",
    "sudo -n passwd",
    "sudo -n chmod",
    "sudo -n chown",
    "sudo -n crontab",
    "( sudo -n crontab",
    "mkdir -p /tmp/purplelab && echo",
    "sudo -n systemctl",
    "sudo -n at ",
    "sudo -n atq",
    "sudo -n atrm",
    "sudo -n rm -f /tmp/purplelab",
    "sudo -n rm -rf /tmp/purplelab",
    "mkdir -p /tmp/purplelab",
    "echo",
    "for i in",
    "sshpass",
    "id ",
    "whoami",
    "ls -la",
    "stat ",
    "getfacl",
    "last -F",
    "lastb -F",
    "who",
    "uptime",
]


class SSHCommandNotAllowed(Exception):
    pass


class SSHHostNotAllowed(Exception):
    pass


class LabSSHClient:
    """A guarded SSH session to a single lab VM."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 key_path: Optional[str] = None):
        settings = get_settings()
        self.host = host or settings.lab_vm_host
        self.port = port or settings.lab_vm_port
        self.username = username or settings.lab_vm_username
        self.password = password or settings.lab_vm_password
        self.key_path = key_path or settings.lab_vm_ssh_key_path
        self._allowed_hosts = settings.allowed_lab_hosts_list
        self._client: Optional[paramiko.SSHClient] = None

    def connect(self) -> None:
        if self.host not in self._allowed_hosts:
            raise SSHHostNotAllowed(
                f"Refusing to connect: '{self.host}' is not in ALLOWED_LAB_HOSTS "
                f"({self._allowed_hosts}). Update your .env if this is really your lab VM."
            )

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = dict(hostname=self.host, port=self.port, username=self.username, timeout=10)
        if self.key_path:
            connect_kwargs["pkey"] = paramiko.RSAKey.from_private_key_file(
                _expand(self.key_path)
            )
        elif self.password:
            connect_kwargs["password"] = self.password
        else:
            raise ValueError("No SSH credential configured (set LAB_VM_PASSWORD or LAB_VM_SSH_KEY_PATH)")

        client.connect(**connect_kwargs)
        self._client = client
        logger.info("Connected to lab VM %s@%s:%s", self.username, self.host, self.port)

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "LabSSHClient":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _assert_client(self) -> paramiko.SSHClient:
        if not self._client:
            raise RuntimeError("SSH client is not connected. Call connect() first.")
        return self._client

    def run(self, command: str, timeout: int = 20) -> "CommandResult":
        """
        Execute a single, pre-approved shell command on the lab VM.

        Raises SSHCommandNotAllowed if the command does not match the
        ALLOWED_COMMAND_PREFIXES allow-list. This is intentional - see the
        module docstring.
        """
        if not any(command.strip().startswith(p) for p in ALLOWED_COMMAND_PREFIXES):
            raise SSHCommandNotAllowed(
                f"Command rejected by allow-list: {command!r}. "
                "PurpleLab AI only runs commands defined in app/scenarios/definitions.py."
            )

        client = self._assert_client()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        logger.debug("Executed on %s: %s (exit=%s)", self.host, command, exit_code)
        return CommandResult(command=command, stdout=out, stderr=err, exit_code=exit_code)

    def fetch_file_text(self, remote_path: str, max_bytes: int = 2_000_000) -> str:
        """Read a remote text file (e.g. a log file) via SFTP, capped in size."""
        client = self._assert_client()
        sftp = client.open_sftp()
        try:
            with sftp.open(remote_path, "r") as f:
                data = f.read(max_bytes)
        finally:
            sftp.close()
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        return data


class CommandResult:
    def __init__(self, command: str, stdout: str, stderr: str, exit_code: int):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def __repr__(self) -> str:
        return f"<CommandResult exit={self.exit_code} cmd={self.command!r}>"


def _expand(path: str) -> str:
    import os
    return os.path.expanduser(path)
