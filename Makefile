SHELL := /bin/sh

BACKEND_VENV := backend/.venv
PYTHON := $(BACKEND_VENV)/bin/python
PIP := $(BACKEND_VENV)/bin/pip
PYTEST := $(BACKEND_VENV)/bin/pytest
UVICORN := $(BACKEND_VENV)/bin/uvicorn
ALEMBIC := $(BACKEND_VENV)/bin/alembic

.PHONY: setup migrate backend frontend dev test build worker-once clean-db

setup:
	python3 -m venv $(BACKEND_VENV)
	$(PIP) install -r backend/requirements.txt
	cd frontend && npm install

migrate:
	$(ALEMBIC) upgrade head

backend:
	$(ALEMBIC) upgrade head
	$(UVICORN) app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5174

dev:
	@printf '%s\n' 'Run these in two terminals:'
	@printf '%s\n' '  make backend'
	@printf '%s\n' '  make frontend'

test:
	$(PYTEST) backend/tests -q

build:
	cd frontend && npm run build

worker-once:
	PYTHONPATH=backend $(PYTHON) -m app.worker

clean-db:
	rm -f workpilot.db backend/workpilot.db
