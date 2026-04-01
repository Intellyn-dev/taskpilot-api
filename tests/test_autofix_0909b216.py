import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import User

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

def test_get_user_profile_without_company_should_not_crash(client):
    """Test that get_user does not crash when user has no associated company."""
    # Create a user without a company
    response = client.post("/", json={"name": "No Company User", "email": "nocompany@example.com", "role": "member"})
    user_id = response.json()["id"]

    # This should not raise AttributeError: 'NoneType' object has no attribute 'name'
    response = client.get(f"/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "No Company User"
    assert data["email"] == "nocompany@example.com"
    assert "avatar_url" in data
    assert "bio" in data