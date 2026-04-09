import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, UserProfile

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

def test_get_user_without_profile_returns_none_fields():
    """Test that get_user handles missing profile gracefully by returning None for avatar_url and empty string for bio."""
    db = TestingSessionLocal()
    user = User(name="No Profile User", email="noprofile@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] is None
    assert data["bio"] == ""

    db.delete(user)
    db.commit()
    db.close()

def test_update_profile_for_user_without_existing_profile_creates_new_profile():
    """Test that update_profile creates a new profile when user has no existing profile."""
    db = TestingSessionLocal()
    user = User(name="New Profile User", email="newprofile@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.put(f"/users/{user.id}/profile", params={"bio": "New bio", "avatar_url": "http://example.com/avatar.png"})
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "New bio"
    assert data["avatar_url"] == "http://example.com/avatar.png"

    db.refresh(user)
    assert user.profile is not None
    assert user.profile.bio == "New bio"
    assert user.profile.avatar_url == "http://example.com/avatar.png"

    db.delete(user.profile)
    db.delete(user)
    db.commit()
    db.close()