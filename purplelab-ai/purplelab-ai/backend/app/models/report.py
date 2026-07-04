"""
models/report.py
=================
Metadata record for a generated HTML/PDF report so past reports can be
listed and re-downloaded from the Report Generator UI.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("scenario_runs.id"), nullable=False)
    format = Column(String, nullable=False)  # "html" | "pdf"
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
