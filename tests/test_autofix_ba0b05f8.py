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

def test_get_user_without_profile_reproduces_bug():
    """Reproduces the original bug: AttributeError when user.profile is None."""
    db = next(override_get_db())
    user = User(name="NoProfile", email="noprofile@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] is None
    assert data["bio"] == ""

def test_get_user_with_profile_verifies_fix():
    """Verifies the fix works: user with profile returns correct data."""
    db = next(override_get_db())
    user = User(name="WithProfile", email="withprofile@example.com", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)

    client.put(f"/users/{user.id}/profile", json={"bio": "Test bio", "avatar_url": "http://example.com/avatar.png"})
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] == "http://example.com/avatar.png"
    assert data["bio"] == "Test bio"