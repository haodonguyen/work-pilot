from pydantic import BaseModel


class DashboardOut(BaseModel):
    todays_jobs: int
    upcoming_bookings: int
    pending_quotes: int
    overdue_invoices: int
    automation_events: int
    estimated_admin_minutes_saved: int
