from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models import AutomationEvent, AutomationRule, Job, JobStatus, Quote, QuoteStatus, TemplateType


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
    {
        "name": "Quote follow-up",
        "trigger": "quote.pending",
        "condition": "Quote is sent and still valid",
        "action": "Generate quote follow-up message",
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
    (
        TemplateType.quote_follow_up,
        "Quote follow-up",
        "Hi {{customerName}}, just checking whether you had any questions about quote {{quoteNumber}}.",
    ),
]


def seed_default_rules(db: Session, business_id: int) -> None:
    for rule in DEFAULT_RULES:
        db.add(AutomationRule(business_id=business_id, **rule))


def render_job_message(prefix: str, job: Job) -> str:
    return f"{prefix} generated for {job.customer.name}: {job.service_type} on {job.scheduled_at:%d %b %Y at %I:%M %p}"


def render_quote_followup(quote: Quote) -> str:
    return f"Quote follow-up generated for {quote.customer.name}: {quote.number} for {quote.service_type}"


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


def handle_pending_quote_followups(db: Session, business_id: int) -> list[AutomationEvent]:
    any_rule = (
        db.query(AutomationRule)
        .filter_by(business_id=business_id, trigger="quote.pending")
        .first()
    )
    if any_rule is None:
        any_rule = AutomationRule(
            business_id=business_id,
            name="Quote follow-up",
            trigger="quote.pending",
            condition="Quote is sent and still valid",
            action="Generate quote follow-up message",
        )
        db.add(any_rule)
        db.flush()

    rule = (
        db.query(AutomationRule)
        .filter_by(business_id=business_id, trigger="quote.pending", enabled=True)
        .first()
    )
    if rule is None:
        return []

    quotes = (
        db.query(Quote)
        .options(joinedload(Quote.customer))
        .filter(
            Quote.business_id == business_id,
            Quote.status == QuoteStatus.sent,
            Quote.valid_until >= date.today(),
        )
        .order_by(Quote.valid_until)
        .all()
    )
    events: list[AutomationEvent] = []
    for quote in quotes:
        message = render_quote_followup(quote)
        existing = (
            db.query(AutomationEvent)
            .filter_by(business_id=business_id, rule_id=rule.id, message=message)
            .first()
        )
        if existing is not None:
            continue
        event = AutomationEvent(
            business_id=business_id,
            rule_id=rule.id,
            message=message,
        )
        db.add(event)
        events.append(event)
    return events
