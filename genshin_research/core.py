import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    return result.astimezone(timezone.utc)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as stream:
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
            "Document the requested data-use scope and policy review; packages require retention of 1-30 days"
        )


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value, *, ensure_ascii=True):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=ensure_ascii) + "\n", encoding="utf-8"
    )
