import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.models import User, Company

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

def test_get_user_profile_without_company_reproduces_bug(client):
    """Reproduces the bug where get_user_profile fails when user has no company."""
    db = TestingSessionLocal()
    user = User(name="Alice", email="alice@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "member"
    assert data["avatar_url"] is None
    assert data["bio"] is None

def test_get_user_profile_with_company_works_after_fix(client):
    """Verifies the fix works when user has a company."""
    db = TestingSessionLocal()
    company = Company(name="Acme Inc.")
    db.add(company)
    db.commit()
    db.refresh(company)
    user = User(name="Bob", email="bob@example.com", role="admin", company_id=company.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["name"] == "Bob"
    assert data["email"] == "bob@example.com"
    assert data["role"] == "admin"
    assert data["avatar_url"] is None
    assert data["bio"] is None