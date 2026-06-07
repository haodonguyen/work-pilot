from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_headers():
    email = f"ava-{uuid4().hex}@example.com"
    register = client.post(
        "/auth/register",
        json={
            "business_name": "Sparkle Home Cleaning",
            "name": "Ava Owner",
            "email": email,
            "password": "password123",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_register_login_and_me():
    headers = auth_headers()
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"].startswith("ava-")
    assert response.json()["business"]["name"] == "Sparkle Home Cleaning"


def test_customer_and_job_create_generate_dashboard_activity():
    headers = auth_headers()
    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "name": "Sarah Nguyen",
            "email": "sarah@example.com",
            "phone": "0400 111 222",
            "address": "12 Market Street, Richmond VIC",
            "notes": "Prefers morning cleans",
        },
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]

    job = client.post(
        "/jobs",
        headers=headers,
        json={
            "customer_id": customer_id,
            "service_type": "Regular clean",
            "scheduled_at": "2026-06-04T09:00:00",
            "price": 180,
            "status": "scheduled",
            "staff_member": "Mia",
            "notes": "Bring eco products",
        },
    )
    assert job.status_code == 201
    assert job.json()["customer"]["name"] == "Sarah Nguyen"

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["upcoming_bookings"] == 1
    assert dashboard.json()["automation_events"] == 1

    events = client.get("/automation-events", headers=headers)
    assert events.status_code == 200
    assert "Booking confirmation" in events.json()[0]["message"]


def test_ai_suggestions_are_based_on_business_activity():
    headers = auth_headers()
    response = client.post("/ai/suggest-automations", headers=headers)
    assert response.status_code == 200
    assert response.json()["suggestions"]


def test_automation_rule_lifecycle_creates_test_event():
    headers = auth_headers()
    created = client.post(
        "/automation-rules",
        headers=headers,
        json={
            "name": "Invoice reminder",
            "trigger": "invoice.overdue",
            "condition": "Invoice is unpaid for 7 days",
            "action": "Generate payment reminder",
            "enabled": True,
        },
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]

    updated = client.put(
        f"/automation-rules/{rule_id}",
        headers=headers,
        json={"enabled": False, "condition": "Invoice is unpaid for 3 days"},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["condition"] == "Invoice is unpaid for 3 days"

    event = client.post(f"/automation-rules/{rule_id}/test", headers=headers)
    assert event.status_code == 200
    assert event.json()["rule_id"] == rule_id
    assert "Generate payment reminder" in event.json()["message"]


def test_disabled_booking_rule_does_not_create_job_event():
    headers = auth_headers()
    rules = client.get("/automation-rules", headers=headers)
    assert rules.status_code == 200
    booking_rule = next(rule for rule in rules.json() if rule["trigger"] == "job.created")

    disabled = client.put(
        f"/automation-rules/{booking_rule['id']}",
        headers=headers,
        json={"enabled": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False

    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "name": "Sarah Nguyen",
            "email": "sarah.paused@example.com",
            "phone": "0400 111 222",
            "address": "12 Market Street, Richmond VIC",
            "notes": "Prefers morning cleans",
        },
    )
    assert customer.status_code == 201

    job = client.post(
        "/jobs",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "service_type": "Regular clean",
            "scheduled_at": "2026-06-04T09:00:00",
            "price": 180,
            "status": "scheduled",
            "staff_member": "Mia",
            "notes": "Bring eco products",
        },
    )
    assert job.status_code == 201

    events = client.get("/automation-events", headers=headers)
    assert events.status_code == 200
    assert events.json() == []

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["automation_events"] == 0


def test_overdue_invoice_updates_dashboard_metric():
    headers = auth_headers()
    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "name": "Mason Property Group",
            "email": "accounts@mason.example",
            "phone": "0400 333 444",
            "address": "45 Collins Street, Melbourne VIC",
            "notes": "Monthly commercial clean",
        },
    )
    assert customer.status_code == 201

    invoice = client.post(
        "/invoices",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "number": "INV-1001",
            "amount": 890,
            "due_date": (date.today() - timedelta(days=3)).isoformat(),
            "status": "sent",
            "notes": "June cleaning package",
        },
    )
    assert invoice.status_code == 201
    assert invoice.json()["number"] == "INV-1001"

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["overdue_invoices"] == 1


def test_pending_quote_updates_dashboard_metric():
    headers = auth_headers()
    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "name": "Greenline Offices",
            "email": "ops@greenline.example",
            "phone": "0400 555 666",
            "address": "88 King Street, Melbourne VIC",
            "notes": "Needs after-hours cleaning",
        },
    )
    assert customer.status_code == 201

    quote = client.post(
        "/quotes",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "number": "QUO-1001",
            "service_type": "Office deep clean",
            "amount": 1250,
            "valid_until": (date.today() + timedelta(days=14)).isoformat(),
            "status": "sent",
            "notes": "Includes windows and carpets",
        },
    )
    assert quote.status_code == 201
    assert quote.json()["number"] == "QUO-1001"

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["pending_quotes"] == 1


def test_pending_quote_metric_excludes_closed_draft_and_expired_quotes():
    headers = auth_headers()
    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "name": "Northside Clinic",
            "email": "ops@northside.example",
            "phone": "0400 777 888",
            "address": "22 Lygon Street, Carlton VIC",
            "notes": "Clinic cleaning quote",
        },
    )
    assert customer.status_code == 201
    customer_id = customer.json()["id"]

    quote_payloads = [
        ("QUO-SENT", "sent", date.today() + timedelta(days=14)),
        ("QUO-DRAFT", "draft", date.today() + timedelta(days=14)),
        ("QUO-ACCEPTED", "accepted", date.today() + timedelta(days=14)),
        ("QUO-DECLINED", "declined", date.today() + timedelta(days=14)),
        ("QUO-EXPIRED", "sent", date.today() - timedelta(days=1)),
    ]
    created_quotes = {}
    for number, status, valid_until in quote_payloads:
        response = client.post(
            "/quotes",
            headers=headers,
            json={
                "customer_id": customer_id,
                "number": number,
                "service_type": "Clinic deep clean",
                "amount": 1450,
                "valid_until": valid_until.isoformat(),
                "status": status,
                "notes": "",
            },
        )
        assert response.status_code == 201
        created_quotes[number] = response.json()

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["pending_quotes"] == 1

    accepted = client.put(
        f"/quotes/{created_quotes['QUO-SENT']['id']}",
        headers=headers,
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["pending_quotes"] == 0


def test_quote_followup_automation_creates_one_event_per_pending_quote():
    headers = auth_headers()
    customer = client.post(
        "/customers",
        headers=headers,
        json={
            "name": "Bright Dental",
            "email": "admin@bright.example",
            "phone": "0400 999 111",
            "address": "10 Chapel Street, South Yarra VIC",
            "notes": "Wants chair room cleaning quote",
        },
    )
    assert customer.status_code == 201

    quote = client.post(
        "/quotes",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "number": "QUO-FOLLOW",
            "service_type": "Dental clinic clean",
            "amount": 1750,
            "valid_until": (date.today() + timedelta(days=7)).isoformat(),
            "status": "sent",
            "notes": "",
        },
    )
    assert quote.status_code == 201

    suggestions = client.post("/ai/suggest-automations", headers=headers)
    assert suggestions.status_code == 200
    assert suggestions.json()["suggestions"][0]["title"] == "Follow up open quotes"

    rules = client.get("/automation-rules", headers=headers)
    assert rules.status_code == 200
    quote_rule = next(rule for rule in rules.json() if rule["trigger"] == "quote.pending")

    first_run = client.post("/automation-rules/run-quote-followups", headers=headers)
    assert first_run.status_code == 200
    assert len(first_run.json()) == 1
    assert first_run.json()[0]["rule_id"] == quote_rule["id"]
    assert "Quote follow-up generated for Bright Dental: QUO-FOLLOW" in first_run.json()[0]["message"]

    second_run = client.post("/automation-rules/run-quote-followups", headers=headers)
    assert second_run.status_code == 200
    assert second_run.json() == []

    disabled = client.put(f"/automation-rules/{quote_rule['id']}", headers=headers, json={"enabled": False})
    assert disabled.status_code == 200

    another_quote = client.post(
        "/quotes",
        headers=headers,
        json={
            "customer_id": customer.json()["id"],
            "number": "QUO-PAUSED",
            "service_type": "Dental reception clean",
            "amount": 620,
            "valid_until": (date.today() + timedelta(days=7)).isoformat(),
            "status": "sent",
            "notes": "",
        },
    )
    assert another_quote.status_code == 201

    paused_run = client.post("/automation-rules/run-quote-followups", headers=headers)
    assert paused_run.status_code == 200
    assert paused_run.json() == []
