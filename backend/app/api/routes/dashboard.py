from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import AutomationEvent, Invoice, InvoiceStatus, Job, JobStatus, Quote, QuoteStatus, User
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
    overdue_invoices = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.business_id == user.business_id,
            Invoice.status == InvoiceStatus.sent,
            Invoice.due_date < date.today(),
        )
        .scalar()
        or 0
    )
    pending_quotes = (
        db.query(func.count(Quote.id))
        .filter(
            Quote.business_id == user.business_id,
            Quote.status == QuoteStatus.sent,
            Quote.valid_until >= date.today(),
        )
        .scalar()
        or 0
    )
    events = db.query(func.count(AutomationEvent.id)).filter_by(business_id=user.business_id).scalar() or 0
    return DashboardOut(
        todays_jobs=len(todays_jobs),
        upcoming_bookings=upcoming,
        pending_quotes=pending_quotes,
        overdue_invoices=overdue_invoices,
        automation_events=events,
        estimated_admin_minutes_saved=events * 5,
    )
