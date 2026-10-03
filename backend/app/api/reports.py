from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.schemas.report import ReportCreate, ReportUpdate, ReportResponse
from backend.app.services import report_service

router = APIRouter(tags=["reports"])

@router.post("/reports/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    return report_service.create_report(db=db, report=report)

@router.get("/reports/", response_model=List[ReportResponse])
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return report_service.get_reports(db, skip=skip, limit=limit)

@router.get("/reports/{report_id}", response_model=ReportResponse)
def read_report(report_id: int, db: Session = Depends(get_db)):
    db_report = report_service.get_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.put("/reports/{report_id}", response_model=ReportResponse)
def update_report(report_id: int, report: ReportUpdate, db: Session = Depends(get_db)):
    db_report = report_service.update_report(db, report_id=report_id, report_update=report)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.delete("/reports/{report_id}", response_model=ReportResponse)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    db_report = report_service.delete_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report