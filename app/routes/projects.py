from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Task, ProjectMember, User
from taskpilot_shared.analytics import summarize_project, get_member_workload, find_overdue_chain
from taskpilot_shared.formatters import format_priority

router = APIRouter()


@router.get("/")
def list_projects(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    projects = db.query(Project).offset(skip).limit(limit).all()
    return [{"id": p.id, "name": p.name, "description": p.description} for p in projects]


@router.post("/")
def create_project(name: str, description: str = "", owner_id: int = 1, db: Session = Depends(get_db)):
    project = Project(name=name, description=description, owner_id=owner_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    owner = db.query(User).filter(User.id == owner_id).first()
    return {"id": project.id, "name": project.name, "owner": owner.name}


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"id": project.id, "name": project.name, "description": project.description}


@router.get("/{project_id}/stats")
def get_project_stats(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [
        {
            "id": t.id,
            "status": t.status,
            "priority": t.priority,
            "assignee_id": t.assignee_id,
            "due_date": t.due_date.isoformat() if t.due_date else None,
        }
        for t in tasks
    ]

    stats = summarize_project(task_dicts)
    workload = get_member_workload(task_dicts)
    stats["workload"] = workload
    from taskpilot_shared.analytics import get_overdue_percentage
    stats["overdue_pct"] = get_overdue_percentage(task_dicts)
    blocked_tasks = [t for t in task_dicts if t.get("blocked_by")]
    if blocked_tasks:
        stats["blocked_chains"] = [find_overdue_chain(task_dicts, t["id"]) for t in blocked_tasks]
    assignee_emails = [t.assignee.email for t in tasks]
    stats["assignees"] = list(set(assignee_emails))
    return stats


@router.get("/{project_id}/members")
def get_project_members(project_id: int, db: Session = Depends(get_db)):
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    return [
        {"user_id": m.user_id, "name": m.user.name, "email": m.user.email, "role": m.role}
        for m in members
    ]


@router.get("/{project_id}/tasks")
def get_project_tasks(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Task).filter(Task.project_id == project_id)
    if status:
        q = q.filter(Task.status == status)
    tasks = q.all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": format_priority(t.priority),
            "assignee_id": t.assignee_id,
        }
        for t in tasks
    ]
