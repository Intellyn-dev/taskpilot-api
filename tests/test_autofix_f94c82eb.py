import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.routes.users import router

app = FastAPI()
app.include_router(router, prefix="/users")

client = TestClient(app)


def make_mock_user(with_company=True, with_profile=True):
    """Helper to create a mock User object for testing."""
    user = MagicMock()
    user.id = 1
    user.name = "Alice"
    user.email = "alice@example.com"
    user.role = "member"

    if with_profile:
        user.profile = MagicMock()
        user.profile.avatar_url = "https://example.com/avatar.png"
        user.profile.bio = "Engineer"
    else:
        user.profile = None

    if with_company:
        user.company = MagicMock()
        user.company.name = "Acme Corp"
    else:
        user.company = None

    return user


def get_mock_db():
    return MagicMock(spec=Session)


def test_get_user_profile_reproduces_bug_when_company_is_none():
    """
    Regression test: Reproduces the AttributeError: 'NoneType' object has no
    attribute 'name' bug that occurred in get_user_profile (users.py, line 45)
    when user.company is None and the code attempted to access user.company.name
    without a None guard. Before the fix, this would raise a 500 error due to
    the AttributeError. After the fix, it should return 200 with company=None.
    """
    mock_user = make_mock_user(with_company=False, with_profile=True)
    mock_db = get_mock_db()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_user

    with patch("app.routes.users.get_db", return_value=mock_db):
        response = client.get("/users/1")

    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}. "
        "This likely means the AttributeError on user.company.name is still present."
    )
    data = response.json()
    assert data["company"] is None, (
        f"Expected company to be None when user.company is None, got: {data.get('company')}"
    )


def test_get_user_profile_returns_company_name_when_company_exists():
    """
    Verification test: Confirms the fix correctly returns the company name
    when user.company is not None, ensuring the None guard does not break
    the happy path where a user has an associated company.
    """
    mock_user = make_mock_user(with_company=True, with_profile=True)
    mock_db = get_mock_db()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_user

    with patch("app.routes.users.get_db", return_value=mock_db):
        response = client.get("/users/1")

    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "Acme Corp", (
        f"Expected company name 'Acme Corp' but got: {data.get('company')}"
    )
    assert data["id"] == 1
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["bio"] == "Engineer"
    assert data["avatar_url"] == "https://example.com/avatar.png"