import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.routes.projects import create_project


def make_mock_db(user_return_value):
    """Helper to build a mock db that returns a given value for User queries."""
    db = MagicMock(spec=Session)

    project_mock = MagicMock()
    project_mock.id = 1
    project_mock.name = "Test Project"

    query_mock = MagicMock()
    filter_mock = MagicMock()

    def query_side_effect(model):
        from app.models import User, Project
        if model is User:
            user_query = MagicMock()
            user_filter = MagicMock()
            user_filter.first.return_value = user_return_value
            user_query.filter.return_value = user_filter
            return user_query
        if model is Project:
            proj_query = MagicMock()
            return proj_query
        return query_mock

    db.query.side_effect = query_side_effect
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, "id", 1) or setattr(obj, "name", "Test Project"))

    return db


def test_create_project_reproduces_bug_when_owner_not_found():
    """
    Reproduces the original bug: when db.query(User).filter(...).first() returns None,
    accessing owner.name raises AttributeError because owner is None.
    Before the fix, this would raise AttributeError instead of HTTPException(404).
    After the fix, this should raise HTTPException with status_code=404.
    """
    db = make_mock_db(user_return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        create_project(name="Test Project", description="desc", owner_id=999, db=db)

    assert exc_info.value.status_code == 404
    assert "owner_id" in exc_info.value.detail.lower() or "user" in exc_info.value.detail.lower()


def test_create_project_succeeds_when_owner_exists():
    """
    Verifies the fix works correctly: when a valid owner_id is provided and the User
    exists in the database, create_project returns the expected response including
    the owner's name without raising any error.
    """
    owner_mock = MagicMock()
    owner_mock.name = "Alice"

    db = make_mock_db(user_return_value=owner_mock)

    result = create_project(name="Test Project", description="desc", owner_id=1, db=db)

    assert result["name"] == "Test Project"
    assert result["owner"] == "Alice"
    assert "id" in result