from sqlalchemy.orm import Session
from backend.app.models.report import Report
from backend.app.schemas.report import ReportCreate, ReportUpdate

def get_report(db: Session, report_id: int):
    return db.query(Report).filter(Report.id == report_id).first()

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Report).offset(skip).limit(limit).all()

def create_report(db: Session, report: ReportCreate):
    db_report = Report(
        title=report.title,
        description=report.description,
        content=report.content,
        status=report.status
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def update_report(db: Session, report_id: int, report_update: ReportUpdate):
    db_report = get_report(db, report_id)
    if not db_report:
        return None
    
    update_data = report_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_report, key, value)
        
    db.commit()
    db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: int):
    db_report = get_report(db, report_id)
    if not db_report:
        return None
    
    db.delete(db_report)
    db.commit()
    return db_report
