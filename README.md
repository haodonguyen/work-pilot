# WorkPilot

WorkPilot is an AI automation platform MVP for small Australian service businesses. It helps teams manage customers and jobs, simulate booking confirmations and review requests, view automation activity, and surface AI-style workflow suggestions.

## Current MVP

- FastAPI backend with JWT-style bearer authentication
- Business-scoped owner accounts
- Customer CRUD
- Job CRUD with simulated automation events
- Dashboard metrics and estimated admin time saved
- Default automation rules and message templates
- React + TypeScript frontend with a Stitch-inspired landing page and operational dashboard
- Docker Compose path for API, frontend, PostgreSQL, and Redis

## Run Locally

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

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
- `GET /dashboard`
- `GET /automation-rules`
- `GET /automation-events`
- `GET /templates`
- `POST /ai/suggest-automations`

## Next Milestones

1. Add Alembic migrations and switch local dev to PostgreSQL by default.
2. Add quote and invoice models with overdue follow-up rules.
3. Add Celery worker tasks for scheduled reminders.
4. Replace simulated AI suggestions with OpenAI API integration.
5. Expand tests around permissions, update/delete flows, and automation edge cases.
