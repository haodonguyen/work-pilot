from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai, auth, automations, customers, dashboard, jobs, templates
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WorkPilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(jobs.router)
app.include_router(automations.router)
app.include_router(templates.router)
app.include_router(dashboard.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"status": "ok"}
