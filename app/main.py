from __future__ import annotations

import os
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import engine, Base
from app.routes import projects, tasks, users

load_dotenv()

dsn = os.getenv("GLITCHTIP_DSN", "")
if dsn:
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=1.0,
        environment=os.getenv("ENVIRONMENT", "development"),
        send_default_pii=True,
    )

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/health")
def health():
    return {"status": "ok"}
