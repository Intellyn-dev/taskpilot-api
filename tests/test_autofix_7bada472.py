import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import User, Company

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

def test_get_user_profile_without_company_reproduces_bug(client):
    """Reproduces the bug where get_user_profile fails when user has no company."""
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
    assert data["avatar_url"] is None
    assert data["bio"] is None

def test_get_user_profile_with_company_works_after_fix(client):
    """Verifies the fix works when user has an associated company."""
    db = next(override_get_db())
    company = Company(name="Test Company")
    db.add(company)
    db.commit()
    db.refresh(company)
    user = User(name="Test User", email="test@example.com", role="member", company_id=company.id)
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
    assert data["avatar_url"] is None
    assert data["bio"] is None