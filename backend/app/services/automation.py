from sqlalchemy.orm import Session

from app.models import AutomationEvent, AutomationRule, Job, JobStatus, TemplateType


DEFAULT_RULES = [
    {
        "name": "Booking confirmation",
        "trigger": "job.created",
        "condition": "Job status is scheduled",
        "action": "Generate booking confirmation message",
    },
    {
        "name": "Review request",
        "trigger": "job.completed",
        "condition": "No review request has been sent",
        "action": "Generate review request message",
    },
    {
        "name": "Appointment reminder",
        "trigger": "job.reminder_due",
        "condition": "Job is scheduled or confirmed within 24 hours",
        "action": "Generate appointment reminder",
    },
]


DEFAULT_TEMPLATES = [
    (
        TemplateType.booking_confirmation,
        "Booking confirmation",
        "Hi {{customerName}}, your {{serviceType}} booking is scheduled for {{jobDate}} at {{jobTime}}.",
    ),
    (
        TemplateType.appointment_reminder,
        "24-hour reminder",
        "Hi {{customerName}}, this is a reminder for your {{serviceType}} booking on {{jobDate}} at {{jobTime}}.",
    ),
    (
        TemplateType.review_request,
        "Review request",
        "Hi {{customerName}}, thanks for choosing us. Would you mind leaving a quick review?",
    ),
]


def seed_default_rules(db: Session, business_id: int) -> None:
    for rule in DEFAULT_RULES:
        db.add(AutomationRule(business_id=business_id, **rule))


def render_job_message(prefix: str, job: Job) -> str:
    return f"{prefix} generated for {job.customer.name}: {job.service_type} on {job.scheduled_at:%d %b %Y at %I:%M %p}"


def handle_job_created(db: Session, job: Job) -> None:
    if job.status != JobStatus.scheduled:
        return
    rule = (
        db.query(AutomationRule)
        .filter_by(business_id=job.business_id, trigger="job.created", enabled=True)
        .first()
    )
    if rule is None:
        return
    db.add(
        AutomationEvent(
            business_id=job.business_id,
            rule_id=rule.id,
            job_id=job.id,
            message=render_job_message("Booking confirmation", job),
        )
    )


def handle_job_completed(db: Session, job: Job) -> None:
    rule = (
        db.query(AutomationRule)
        .filter_by(business_id=job.business_id, trigger="job.completed", enabled=True)
        .first()
    )
    if rule is None:
        return
    db.add(
        AutomationEvent(
            business_id=job.business_id,
            rule_id=rule.id,
            job_id=job.id,
            message=render_job_message("Review request", job),
        )
    )
