"""
main.py
========
PurpleLab AI - FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

See README.md for full setup instructions, including how to point this at
your isolated lab VM.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import analytics, copilot, events, mitre, reports, scenarios
from app.utils.logger import configure_logging

configure_logging()
logger = logging.getLogger("purplelab.main")

settings = get_settings()

app = FastAPI(
    title="PurpleLab AI",
    description=(
        "Educational Purple Team platform for authorized, isolated lab "
        "environments. Executes predefined training scenarios over SSH, "
        "maps observed activity to MITRE ATT&CK, and generates AI-assisted "
        "explanations, detection guidance, and reports."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("PurpleLab AI backend started (env=%s)", settings.app_env)
    logger.info("Configured lab target: %s (allow-listed hosts: %s)",
                settings.lab_vm_host, settings.allowed_lab_hosts_list)


app.include_router(scenarios.router)
app.include_router(events.router)
app.include_router(mitre.router)
app.include_router(copilot.router)
app.include_router(reports.router)
app.include_router(analytics.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PurpleLab AI", "env": settings.app_env}
