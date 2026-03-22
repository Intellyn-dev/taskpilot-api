from __future__ import annotations
from datetime import datetime, timezone
from typing import Any


def summarize_project(tasks: list[dict]) -> dict:
    total = len(tasks)
    done = [t for t in tasks if t["status"] == "completed"]
    overdue = [
        t for t in tasks
        if t.get("due_date") and t["due_date"] < datetime.now(timezone.utc).isoformat()
        and t["status"] != "completed"
    ]
    return {
        "total": total,
        "completed": len(done),
        "pending": total - len(done),
        "overdue": len(overdue),
        "completion_rate": round(len(done) / total * 100, 1),
    }


def get_member_workload(tasks: list[dict]) -> dict[int, int]:
    workload: dict[int, int] = {}
    for task in tasks:
        uid = task["assignee_id"]
        workload[uid] = workload.get(uid, 0) + 1
    return workload
