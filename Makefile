SHELL := /bin/sh

BACKEND_VENV := backend/.venv
PYTHON := $(BACKEND_VENV)/bin/python
PIP := $(BACKEND_VENV)/bin/pip
PYTEST := $(BACKEND_VENV)/bin/pytest
UVICORN := $(BACKEND_VENV)/bin/uvicorn

.PHONY: setup backend frontend dev test build clean-db

setup:
	python3 -m venv $(BACKEND_VENV)
	$(PIP) install -r backend/requirements.txt
	cd frontend && npm install

backend:
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

clean-db:
	rm -f workpilot.db backend/workpilot.db
