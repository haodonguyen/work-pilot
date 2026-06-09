# MVP Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make WorkPilot's first MVP deployable with scheduled automation, database migrations, Render configuration, and release documentation.

**Architecture:** Keep the MVP operationally simple. Add a one-shot worker command that can be run manually, by cron, or by Render Cron Jobs, and keep the existing API routes as the main user-facing surface. Add Alembic for repeatable schema creation while retaining local SQLite support.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, SQLite/PostgreSQL, React/Vite, Render Blueprint.

---

### Task 1: Scheduled Automation Worker

**Files:**
- Modify: `backend/tests/test_mvp.py`
- Modify: `backend/app/services/automation.py`
- Create: `backend/app/worker.py`
- Modify: `Makefile`

- [ ] Add failing tests for appointment reminders, overdue invoice reminders, duplicate protection, disabled rules, and worker summary counts.
- [ ] Implement service functions for due job reminders and overdue invoice reminders.
- [ ] Implement `app.worker.run_once()`.
- [ ] Add `make worker-once`.

### Task 2: Deployment And Migrations

**Files:**
- Modify: `backend/requirements.txt`
- Create: `alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/20260609_0001_initial_schema.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Create: `render.yaml`
- Modify: `.env.example`
- Modify: `README.md`

- [ ] Add Alembic dependency and initial migration.
- [ ] Add configurable CORS origins.
- [ ] Add Render Blueprint for API, static frontend, Postgres, and cron worker.
- [ ] Document deployment env vars and release checks.

### Task 3: Verification And Publish

**Files:**
- Modify: `tasks/todo.md`

- [ ] Run `make test`.
- [ ] Run `make build`.
- [ ] Inspect `git diff`.
- [ ] Commit and push to `origin/main`.

