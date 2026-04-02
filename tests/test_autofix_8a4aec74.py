import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.routes.tasks import router

app = FastAPI()
app.include_router(router, prefix="/tasks")


def make_mock_task(task_id, title, status, priority, assignee=None):
    task = MagicMock()
    task.id = task_id
    task.title = title
    task.status = status
    task.priority = priority
    task.assignee = assignee
    return task


def get_test_client(mock_tasks):
    def override_get_db():
        db = MagicMock(spec=Session)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = mock_tasks
        db.query.return_value = query_mock
        yield db

    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    app.dependency_overrides.clear()
    return client, override_get_db


def test_list_tasks_unassigned_reproduces_bug():
    """
    Regression test that reproduces the original bug:
    When a task has assignee=None (assignee_id is nullable), accessing t.assignee.name
    raises AttributeError: 'NoneType' object has no attribute 'name', causing a 500 error.
    This test should FAIL before the fix (500 response) and PASS after the fix (200 response).
    """
    unassigned_task = make_mock_task(
        task_id=1,
        title="Unassigned Task",
        status="todo",
        priority="medium",
        assignee=None,
    )

    from app.database import get_db

    def override_get_db():
        db = MagicMock(spec=Session)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [unassigned_task]
        db.query.return_value = query_mock
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/")

    app.dependency_overrides.clear()

    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}. "
        "This indicates the bug is present: accessing .name on None assignee causes a 500 error."
    )


def test_list_tasks_unassigned_returns_null_assignee_name():
    """
    Regression test that verifies the fix works correctly:
    When a task has assignee=None, the endpoint should return assignee_name as None
    in the response rather than raising an AttributeError.
    Also verifies that tasks with an assigned user still return the correct assignee_name.
    """
    mock_assignee = MagicMock()
    mock_assignee.name = "Alice"

    assigned_task = make_mock_task(
        task_id=1,
        title="Assigned Task",
        status="in_progress",
        priority="high",
        assignee=mock_assignee,
    )
    unassigned_task = make_mock_task(
        task_id=2,
        title="Unassigned Task",
        status="todo",
        priority="medium",
        assignee=None,
    )

    from app.database import get_db

    def override_get_db():
        db = MagicMock(spec=Session)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [assigned_task, unassigned_task]
        db.query.return_value = query_mock
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/tasks/")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    assigned_result = next(t for t in data if t["id"] == 1)
    assert assigned_result["assignee_name"] == "Alice"

    unassigned_result = next(t for t in data if t["id"] == 2)
    assert unassigned_result["assignee_name"] is None, (
        "Expected assignee_name to be None for a task with no assignee, "
        "but got a non-None value. The fix should return None instead of raising AttributeError."
    )