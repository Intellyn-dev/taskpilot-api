# TaskPilot API

FastAPI-based project and task management backend.

## Setup

```bash
cd ../taskpilot-shared && pip install -e .
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GlitchTip DSN
python seed.py
uvicorn app.main:app --port 8001 --reload
```

## Endpoints

- `GET /projects/` — list projects
- `GET /projects/{id}/stats` — project statistics
- `GET /projects/{id}/tasks` — tasks in project
- `GET /users/{id}` — user profile
- `POST /tasks/` — create task
