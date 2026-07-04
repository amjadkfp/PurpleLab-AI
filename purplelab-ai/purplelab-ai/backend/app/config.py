"""
config.py
=========
Centralized, typed application configuration.

All environment-driven settings live here so the rest of the codebase never
touches `os.environ` directly. This makes the safety guardrails (allowed lab
hosts, credential handling) auditable in a single place.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Lab VM connection ---------------------------------------------
    lab_vm_host: str = "192.168.56.11"
    lab_vm_port: int = 22
    lab_vm_username: str = "labadmin"
    lab_vm_password: Optional[str] = None
    lab_vm_ssh_key_path: Optional[str] = None

    # --- Database ---------------------------------------------------------
    database_url: str = "sqlite:///./purplelab.db"

    # --- AI Copilot ---------------------------------------------------------
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-6"

    # --- App ---------------------------------------------------------
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    reports_dir: str = "./reports"

    # --- Safety guardrails ---------------------------------------------------
    # Comma separated allow-list of hosts PurpleLab AI may open an SSH
    # session to. This is a hard stop enforced in core/ssh_client.py -
    # it exists so the tool can never be pointed at a host outside the
    # user's declared lab environment, intentionally or by typo.
    allowed_lab_hosts: str = "192.168.56.11"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_lab_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.allowed_lab_hosts.split(",") if h.strip()]

    @property
    def reports_path(self) -> Path:
        p = Path(self.reports_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
