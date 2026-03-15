#!/usr/bin/env python3
from app.database import engine, Base, SessionLocal
from app.models import User, Project, Task, ProjectMember

Base.metadata.create_all(bind=engine)

db = SessionLocal()

alice = User(name="Alice Chen", email="alice@example.com", role="admin")
bob = User(name="Bob Smith", email="bob@example.com", role="member")
carol = User(name="Carol White", email="carol@example.com", role="member")
db.add_all([alice, bob, carol])
db.commit()

project1 = Project(name="Platform Revamp", description="Modernize the core platform", owner_id=alice.id)
project2 = Project(name="Mobile App", description="New mobile application", owner_id=bob.id)
db.add_all([project1, project2])
db.commit()

db.add(ProjectMember(project_id=project1.id, user_id=alice.id, role="owner"))
db.add(ProjectMember(project_id=project1.id, user_id=bob.id, role="contributor"))
db.add(ProjectMember(project_id=project2.id, user_id=bob.id, role="owner"))
db.add(ProjectMember(project_id=project2.id, user_id=carol.id, role="contributor"))
db.commit()

tasks = [
    Task(title="Set up CI/CD pipeline", status="completed", priority="high", project_id=project1.id, assignee_id=alice.id),
    Task(title="Refactor authentication module", status="in_progress", priority="high", project_id=project1.id, assignee_id=bob.id),
    Task(title="Write API documentation", status="todo", priority="medium", project_id=project1.id),
    Task(title="Design system components", status="in_progress", priority="medium", project_id=project2.id, assignee_id=carol.id),
    Task(title="Push notifications integration", status="todo", priority="critical", project_id=project2.id),
    Task(title="Performance benchmarks", status="todo", priority="low", project_id=project2.id),
]
db.add_all(tasks)
db.commit()
db.close()
print("Database seeded successfully")
