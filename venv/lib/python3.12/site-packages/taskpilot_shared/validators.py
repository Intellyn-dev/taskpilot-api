from __future__ import annotations
import re
from datetime import datetime


EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def validate_due_date(date_str: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {date_str!r}")


def validate_priority(priority: str) -> str:
    allowed = {"low", "medium", "high", "critical"}
    if priority not in allowed:
        raise ValueError(f"Invalid priority {priority!r}. Must be one of {allowed}")
    return priority
