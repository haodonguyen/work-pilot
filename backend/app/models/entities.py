from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class JobStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class TemplateType(str, Enum):
    booking_confirmation = "booking_confirmation"
    appointment_reminder = "appointment_reminder"
    quote_follow_up = "quote_follow_up"
    invoice_reminder = "invoice_reminder"
    review_request = "review_request"


class InvoiceStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    void = "void"


class QuoteStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"
    declined = "declined"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    users: Mapped[list["User"]] = relationship(back_populates="business")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(50), default="owner")
    business: Mapped[Business] = relationship(back_populates="users")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    jobs: Mapped[list["Job"]] = relationship(back_populates="customer")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="customer")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="customer")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    service_type: Mapped[str] = mapped_column(String(160))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    price: Mapped[float] = mapped_column(Float)
    status: Mapped[JobStatus] = mapped_column(SqlEnum(JobStatus), default=JobStatus.scheduled)
    staff_member: Mapped[str | None] = mapped_column(String(160), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer: Mapped[Customer] = relationship(back_populates="jobs")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    number: Mapped[str] = mapped_column(String(80))
    amount: Mapped[float] = mapped_column(Float)
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[InvoiceStatus] = mapped_column(SqlEnum(InvoiceStatus), default=InvoiceStatus.draft)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer: Mapped[Customer] = relationship(back_populates="invoices")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    number: Mapped[str] = mapped_column(String(80))
    service_type: Mapped[str] = mapped_column(String(160))
    amount: Mapped[float] = mapped_column(Float)
    valid_until: Mapped[date] = mapped_column(Date)
    status: Mapped[QuoteStatus] = mapped_column(SqlEnum(QuoteStatus), default=QuoteStatus.draft)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer: Mapped[Customer] = relationship(back_populates="quotes")


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    type: Mapped[TemplateType] = mapped_column(SqlEnum(TemplateType))
    name: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    trigger: Mapped[str] = mapped_column(String(160))
    condition: Mapped[str] = mapped_column(String(240))
    action: Mapped[str] = mapped_column(String(240))
    enabled: Mapped[bool] = mapped_column(default=True)


class AutomationEvent(Base):
    __tablename__ = "automation_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("automation_rules.id"), nullable=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="simulated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
