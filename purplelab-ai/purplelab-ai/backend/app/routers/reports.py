"""
routers/reports.py
=====================
Generates and serves HTML/PDF reports for a completed scenario run, and
lists previously generated reports.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.report_generator import generate_html_report, generate_pdf_report
from app.database import get_db
from app.models.report import Report
from app.models.scenario_run import ScenarioRun

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/{run_id}/generate")
def generate_report(run_id: str, format: str = "html", db: Session = Depends(get_db)):
    run = db.query(ScenarioRun).filter(ScenarioRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if format not in ("html", "pdf"):
        raise HTTPException(status_code=400, detail="format must be 'html' or 'pdf'")

    try:
        path = generate_html_report(db, run) if format == "html" else generate_pdf_report(db, run)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    report = Report(run_id=run.id, format=format, file_path=str(path))
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "format": report.format, "download_url": f"/api/reports/{report.id}/download"}


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "run_id": r.run_id,
            "format": r.format,
            "created_at": r.created_at,
            "download_url": f"/api/reports/{r.id}/download",
        }
        for r in reports
    ]


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    media_type = "application/pdf" if report.format == "pdf" else "text/html"
    return FileResponse(report.file_path, media_type=media_type, filename=Path(report.file_path).name)
