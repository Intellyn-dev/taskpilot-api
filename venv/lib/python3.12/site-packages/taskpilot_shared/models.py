from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    email: str
    role: str = "member"


class Task(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    project_id: int
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()


class Project(BaseModel):
    id: int
    name: str
    description: str = ""
    owner_id: int
    created_at: datetime = datetime.utcnow()


class Member(BaseModel):
    user_id: int
    project_id: int
    role: str = "contributor"
