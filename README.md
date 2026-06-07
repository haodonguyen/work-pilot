# WorkPilot

WorkPilot is an AI automation platform MVP for small Australian service businesses. It helps teams manage customers, jobs, quotes, invoices, simulated booking confirmations and review requests, automation activity, and AI-style workflow suggestions.

Project location on this machine:

```bash
/Users/haodonguyen/Hao/IT/FlowMate
```

## Current MVP

- FastAPI backend with JWT-style bearer authentication
- Business-scoped owner accounts
- Customer CRUD
- Job CRUD with simulated automation events
- Quote CRUD with pending quote dashboard counts
- Invoice CRUD with overdue dashboard counts
- Quote follow-up automation runner
- Dashboard metrics and estimated admin time saved
- Default automation rules and message templates
- React + TypeScript frontend with a Stitch-inspired landing page and operational dashboard
- Docker Compose path for API, frontend, PostgreSQL, and Redis

## Run Locally

From the project root:

```bash
make setup
```

Start the backend in one terminal:

```bash
make backend
```

Start the frontend in another terminal:

```bash
make frontend
```

Open `http://127.0.0.1:5174/`.

Useful checks:

```bash
make test
make build
```

The default local SQLite database is always stored at the project root as `workpilot.db`, regardless of whether commands are launched from the root or `backend/`.

## Manual Commands

Backend:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Docker:

```bash
docker compose up --build
```

## API Highlights

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET/POST /customers`
- `GET/POST /jobs`
- `GET/POST /quotes`
- `GET/POST /invoices`
- `GET /dashboard`
- `GET /automation-rules`
- `POST /automation-rules/run-quote-followups`
- `GET /automation-events`
- `GET /templates`
- `POST /ai/suggest-automations`

## Next Milestones

1. Add Alembic migrations and switch local dev to PostgreSQL by default.
2. Add Celery worker tasks for scheduled reminders.
3. Replace simulated AI suggestions with OpenAI API integration.
4. Add explicit quote and invoice status transition endpoints.
5. Expand tests around permissions, update/delete flows, and automation edge cases.
