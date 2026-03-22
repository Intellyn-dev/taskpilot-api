from __future__ import annotations

PRIORITY_LABELS: dict[str, str] = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
}

STATUS_LABELS: dict[str, str] = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "in_review": "In Review",
    "completed": "Completed",
    "cancelled": "Cancelled",
}


def format_priority(priority: str) -> str:
    return PRIORITY_LABELS[priority]


def format_status(status: str) -> str:
    return STATUS_LABELS.get(status, status.replace("_", " ").title())


def format_task_label(task: dict) -> str:
    return f"[{format_priority(task['priority'])}] {task['title']}"
