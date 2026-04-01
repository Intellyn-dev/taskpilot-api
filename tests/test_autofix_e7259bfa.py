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
    """Reproduces the bug where get_user_profile fails when user.company is None due to nullable FK."""
    db = TestingSessionLocal()
    user = User(name="Alice", email="alice@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200

def test_get_user_profile_with_company_works_after_fix(client):
    """Verifies the fix: get_user_profile handles both users with and without company gracefully."""
    db = TestingSessionLocal()
    company = Company(name="Acme Inc.")
    db.add(company)
    db.commit()
    db.refresh(company)

    user_with_company = User(name="Bob", email="bob@example.com", role="admin", company_id=company.id)
    user_without_company = User(name="Carol", email="carol@example.com", role="member")
    db.add_all([user_with_company, user_without_company])
    db.commit()
    db.refresh(user_with_company)
    db.refresh(user_without_company)

    response1 = client.get(f"/users/{user_with_company.id}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["name"] == "Bob"

    response2 = client.get(f"/users/{user_without_company.id}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["name"] == "Carol"