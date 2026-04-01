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

def test_get_user_without_company_should_not_raise_attribute_error(client):
    """Test that get_user handles users without a company without raising AttributeError."""
    # Create a user with no company
    response = client.post("/", json={"name": "John Doe", "email": "john@example.com", "role": "member"})
    assert response.status_code == 200
    user_id = response.json()["id"]

    # This should not raise AttributeError: 'NoneType' object has no attribute 'name'
    response = client.get(f"/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["role"] == "member"
    assert "avatar_url" in data
    assert "bio" in data