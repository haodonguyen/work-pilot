from app.core.database import SessionLocal
from app.models import Business
from app.services.automation import (
    handle_due_job_reminders,
    handle_overdue_invoice_reminders,
    handle_pending_quote_followups,
)


def run_once(business_id: int | None = None) -> dict[str, int]:
    db = SessionLocal()
    try:
        business_ids = [business_id] if business_id is not None else [row.id for row in db.query(Business.id).all()]
        summary = {
            "businesses": len(business_ids),
            "appointment_reminders": 0,
            "invoice_reminders": 0,
            "quote_followups": 0,
            "total_events": 0,
        }
        for current_business_id in business_ids:
            appointment_events = handle_due_job_reminders(db, current_business_id)
            invoice_events = handle_overdue_invoice_reminders(db, current_business_id)
            quote_events = handle_pending_quote_followups(db, current_business_id)
            summary["appointment_reminders"] += len(appointment_events)
            summary["invoice_reminders"] += len(invoice_events)
            summary["quote_followups"] += len(quote_events)
        summary["total_events"] = (
            summary["appointment_reminders"]
            + summary["invoice_reminders"]
            + summary["quote_followups"]
        )
        db.commit()
        return summary
    finally:
        db.close()


if __name__ == "__main__":
    print(run_once())

