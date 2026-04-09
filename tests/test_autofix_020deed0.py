import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_get_user_without_company_reproduces_bug():
    """Reproduces the bug where accessing user.company.name raises AttributeError when company is None."""
    db = next(override_get_db())
    user = User(name="Test User", email="test@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["role"] == "member"
    db.close()

def test_get_user_without_company_returns_profile_fields():
    """Verifies that get_user returns None for avatar_url and bio when user has no profile."""
    db = next(override_get_db())
    user = User(name="Test User", email="test@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] is None
    assert data["bio"] is None
    db.close()