import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return result.astimezone(timezone.utc)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields=None):
    rows = list(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def authorize(config, permissions, operation):
    if config["dry_run"]:
        raise PermissionError("Real-data operation disabled in dry-run mode")
    if (
        permissions.get("policy_review_status") != "documented"
        or not permissions.get("evidence_reference")
        or not permissions.get("policy_reviewed_at")
        or not permissions.get(operation)
        or not isinstance(permissions.get("retention_days"), int)
        or isinstance(permissions["retention_days"], bool)
        or not 0 < permissions["retention_days"] <= 30
    ):
        raise PermissionError(
            "Document project-specific permission and policy review; mixed text packages require retention of 1-30 days"
        )


def eligibility(published, updated, video_published, hours=72):
    start = utc(video_published)
    end = start + timedelta(hours=hours)
    if not start <= utc(published) < end:
        return "excluded", "outside_window"
    if utc(updated) >= end:
        return "excluded", "edited_at_or_after_cutoff"
    return "eligible", ""


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value, *, ensure_ascii=True):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=ensure_ascii) + "\n", encoding="utf-8"
    )


def next_month(month):
    """Return YYYY-MM for the following calendar month, including year rollover."""
    year, number = map(int, month.split("-"))
    return f"{year + (number == 12):04d}-{number % 12 + 1:02d}"
