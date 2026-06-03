from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import AutomationEvent, Job, JobStatus, User
from app.schemas.dashboard import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter_by(business_id=user.business_id)
    todays_jobs = [
        job for job in jobs.filter(Job.status.in_([JobStatus.scheduled, JobStatus.confirmed])).all()
        if job.scheduled_at.date() == date.today()
    ]
    upcoming = jobs.filter(Job.status.in_([JobStatus.scheduled, JobStatus.confirmed])).count()
    events = db.query(func.count(AutomationEvent.id)).filter_by(business_id=user.business_id).scalar() or 0
    return DashboardOut(
        todays_jobs=len(todays_jobs),
        upcoming_bookings=upcoming,
        pending_quotes=0,
        overdue_invoices=0,
        automation_events=events,
        estimated_admin_minutes_saved=events * 5,
    )
