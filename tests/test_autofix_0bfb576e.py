import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.routes.tasks import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)


def make_mock_task(due_date=None):
    task = MagicMock()
    task.id = 1
    task.title = "Test Task"
    task.status = "todo"
    task.priority = "medium"
    task.assignee_id = None
    task.project_id = 42
    task.due_date = due_date
    return task


def test_get_task_with_none_due_date_reproduces_bug():
    """
    Reproduces the original bug: get_task calls task.due_date.strftime(...)
    unconditionally. When due_date is None (nullable=True in the Task model),
    this raises AttributeError: 'NoneType' object has no attribute 'strftime'.
    This test should FAIL before the fix (due to AttributeError surfacing as
    a 500 error) and PASS after the fix (returns 200 with due_date=None).
    """
    mock_task = make_mock_task(due_date=None)

    mock_db = MagicMock(spec=Session)
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = mock_task

    with patch("app.routes.tasks.get_db", return_value=mock_db):
        response = client.get("/1")

    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}. "
        "This likely means the bug is present: strftime called on None due_date."
    )
    data = response.json()
    assert data["due_date"] is None


def test_get_task_with_none_due_date_returns_null_in_response():
    """
    Verifies the fix: when a task has due_date=None (created without a due date,
    as allowed by the nullable=True column definition), the get_task endpoint
    must return due_date as null in the JSON response without raising an error.
    The fix adds a conditional check: task.due_date.strftime(...) if task.due_date else None.
    """
    from datetime import datetime

    mock_task_no_due = make_mock_task(due_date=None)
    mock_task_with_due = make_mock_task(due_date=datetime(2024, 6, 15))

    mock_db = MagicMock(spec=Session)
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value

    with patch("app.routes.tasks.get_db", return_value=mock_db):
        mock_filter.first.return_value = mock_task_no_due
        response_no_due = client.get("/1")

        mock_filter.first.return_value = mock_task_with_due
        response_with_due = client.get("/1")

    assert response_no_due.status_code == 200
    data_no_due = response_no_due.json()
    assert data_no_due["due_date"] is None
    assert data_no_due["id"] == 1
    assert data_no_due["title"] == "Test Task"

    assert response_with_due.status_code == 200
    data_with_due = response_with_due.json()
    assert data_with_due["due_date"] == "2024-06-15"