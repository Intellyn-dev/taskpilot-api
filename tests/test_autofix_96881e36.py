import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.models import User, UserProfile
from app.models import Base
from app.routes.users import router

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router, prefix="/users")
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


def test_get_user_without_profile_reproduces_bug(client, db):
    """
    Reproduces the original bug where get_user raises an AttributeError
    (or similar error) when accessing user.profile.avatar_url and user.profile.bio
    without first checking if user.profile is None.

    A user is created without an associated UserProfile record, simulating
    the case where profile is None. Before the fix, accessing user.profile.avatar_url
    would raise an AttributeError because NoneType has no attribute 'avatar_url'.
    After the fix, the endpoint should return empty strings for avatar_url and bio.
    """
    user = User(name="No Profile User", email="noprofile@example.com", role="member")
    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    # Verify no profile exists for this user
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    assert profile is None, "Test setup error: user should not have a profile"

    # Before the fix, this would raise a 500 error due to AttributeError on NoneType
    response = client.get(f"/users/{user_id}")

    # After the fix, this should return 200 with empty strings for profile fields
    assert response.status_code == 200


def test_get_user_without_profile_returns_empty_profile_fields(client, db):
    """
    Verifies the fix works correctly: when a user exists but has no associated
    UserProfile record, the get_user endpoint should return empty strings for
    avatar_url and bio instead of raising an AttributeError.

    The fix adds a None check (user.profile.avatar_url if user.profile else "")
    so that missing profiles are handled gracefully.
    """
    user = User(name="Jane Doe", email="jane@example.com", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    # Confirm no profile record exists
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    assert profile is None, "Test setup error: user should not have a profile"

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"
    assert data["role"] == "admin"
    assert data["avatar_url"] == "", (
        "Expected empty string for avatar_url when user has no profile"
    )
    assert data["bio"] == "", (
        "Expected empty string for bio when user has no profile"
    )