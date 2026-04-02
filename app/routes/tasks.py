from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Task
from taskpilot_shared.validators import validate_priority

router = APIRouter()


@router.get("/")
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    if assignee_id:
        q = q.filter(Task.assignee_id == assignee_id)
    tasks = q.offset(skip).limit(limit).all()
    return [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "assignee_name": t.assignee.name} for t in tasks]


@router.post("/")
def create_task(
    title: str,
    project_id: int,
    priority: str = "medium",
    status: str = "todo",
    assignee_id: Optional[int] = None,
    due_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    priority = validate_priority(priority)
    task = Task(
        title=title,
        project_id=project_id,
        priority=priority,
        status=status,
        assignee_id=assignee_id,
        due_date=datetime.fromisoformat(due_date) if due_date else None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status}


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assignee_id": task.assignee_id,
        "project_id": task.project_id,
        "due_date": task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
    }


@router.patch("/{task_id}/status")
def update_task_status(task_id: int, status: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = status
    db.commit()
    return {"id": task.id, "status": task.status}
