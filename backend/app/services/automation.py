from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models import AutomationEvent, AutomationRule, Invoice, InvoiceStatus, Job, JobStatus, Quote, QuoteStatus, TemplateType


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
        "name": "Invoice reminder",
        "trigger": "invoice.overdue",
        "condition": "Invoice is sent and past its due date",
        "action": "Generate overdue invoice reminder",
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
    (
        TemplateType.invoice_reminder,
        "Invoice reminder",
        "Hi {{customerName}}, this is a friendly reminder that invoice {{invoiceNumber}} is overdue.",
    ),
]


def seed_default_rules(db: Session, business_id: int) -> None:
    for rule in DEFAULT_RULES:
        db.add(AutomationRule(business_id=business_id, **rule))


def render_job_message(prefix: str, job: Job) -> str:
    return f"{prefix} generated for {job.customer.name}: {job.service_type} on {job.scheduled_at:%d %b %Y at %I:%M %p}"


def render_quote_followup(quote: Quote) -> str:
    return f"Quote follow-up generated for {quote.customer.name}: {quote.number} for {quote.service_type}"


def render_invoice_reminder(invoice: Invoice) -> str:
    return f"Invoice reminder generated for {invoice.customer.name}: {invoice.number} due {invoice.due_date:%d %b %Y}"


def ensure_rule(db: Session, business_id: int, rule_definition: dict[str, str]) -> AutomationRule:
    rule = (
        db.query(AutomationRule)
        .filter_by(business_id=business_id, trigger=rule_definition["trigger"])
        .first()
    )
    if rule is None:
        rule = AutomationRule(business_id=business_id, **rule_definition)
        db.add(rule)
        db.flush()
    return rule


def find_enabled_rule(db: Session, business_id: int, trigger: str) -> AutomationRule | None:
    return db.query(AutomationRule).filter_by(business_id=business_id, trigger=trigger, enabled=True).first()


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


def handle_due_job_reminders(db: Session, business_id: int, now: datetime | None = None) -> list[AutomationEvent]:
    now = now or datetime.now()
    ensure_rule(db, business_id, DEFAULT_RULES[2])
    rule = find_enabled_rule(db, business_id, "job.reminder_due")
    if rule is None:
        return []

    jobs = (
        db.query(Job)
        .options(joinedload(Job.customer))
        .filter(
            Job.business_id == business_id,
            Job.status.in_([JobStatus.scheduled, JobStatus.confirmed]),
            Job.scheduled_at >= now,
            Job.scheduled_at <= now + timedelta(hours=24),
        )
        .order_by(Job.scheduled_at)
        .all()
    )
    events: list[AutomationEvent] = []
    for job in jobs:
        message = render_job_message("Appointment reminder", job)
        existing = (
            db.query(AutomationEvent)
            .filter_by(business_id=business_id, rule_id=rule.id, job_id=job.id, message=message)
            .first()
        )
        if existing is not None:
            continue
        event = AutomationEvent(
            business_id=business_id,
            rule_id=rule.id,
            job_id=job.id,
            message=message,
        )
        db.add(event)
        events.append(event)
    return events


def handle_overdue_invoice_reminders(db: Session, business_id: int, today: date | None = None) -> list[AutomationEvent]:
    today = today or date.today()
    ensure_rule(db, business_id, DEFAULT_RULES[3])
    rule = find_enabled_rule(db, business_id, "invoice.overdue")
    if rule is None:
        return []

    invoices = (
        db.query(Invoice)
        .options(joinedload(Invoice.customer))
        .filter(
            Invoice.business_id == business_id,
            Invoice.status == InvoiceStatus.sent,
            Invoice.due_date < today,
        )
        .order_by(Invoice.due_date)
        .all()
    )
    events: list[AutomationEvent] = []
    for invoice in invoices:
        message = render_invoice_reminder(invoice)
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


def handle_pending_quote_followups(db: Session, business_id: int) -> list[AutomationEvent]:
    ensure_rule(db, business_id, DEFAULT_RULES[4])
    rule = find_enabled_rule(db, business_id, "quote.pending")
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
