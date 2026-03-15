from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    role = Column(String(50), default="member")
    created_at = Column(DateTime, default=datetime.utcnow)
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    tasks = relationship("Task", back_populates="assignee")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(Text, default="")
    avatar_url = Column(String(500), default="")
    user = relationship("User", back_populates="profile")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    tasks = relationship("Task", back_populates="project")
    members = relationship("ProjectMember", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(50), default="contributor")
    user = relationship("User")
    project = relationship("Project", back_populates="members")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="todo")
    priority = Column(String(50), default="medium")
    project_id = Column(Integer, ForeignKey("projects.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
