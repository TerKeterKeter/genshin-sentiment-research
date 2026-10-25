"""Register candidate links offline; inclusion always requires human review."""

import csv
import re
from pathlib import Path
from urllib.parse import urlsplit

EVENT_FIELDS = [
    "event_id",
    "character_name",
    "announcement_source_url",
    "initial_announcement_at_utc",
    "video_id",
    "video_url",
    "channel_id",
    "video_published_at_utc",
    "content_type",
    "inclusion_status",
    "exclusion_reason",
    "verification_notes",
]


def video_id_from_input(value):
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    url = urlsplit(value)
    if (
        url.scheme != "https"
        or url.hostname not in {"youtube.com", "www.youtube.com", "m.youtube.com"}
        or url.username
        or url.password
        or url.port
    ):
        raise ValueError("Use an HTTPS YouTube Shorts link or an 11-character video ID")
    match = re.fullmatch(r"/shorts/([A-Za-z0-9_-]{11})/?", url.path)
    if not match:
        raise ValueError("Expected https://youtube.com/shorts/VIDEO_ID")
    return match.group(1)


def register_candidate(value, events="data/events.csv", character=""):
    video_id = video_id_from_input(value)
    path = Path(events).resolve()
    if Path("data").resolve() not in path.parents:
        raise ValueError("Registry must stay within ./data (ignored by Git)")
    if not path.exists():
        raise FileNotFoundError(
            "Registry missing; run python -m genshin_research prepare-audit first"
        )
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if (
            not fields
            or len(fields) != len(set(fields))
            or not set(EVENT_FIELDS) <= set(fields)
        ):
            raise ValueError(
                "Registry headers are incomplete or duplicated; preserve the template columns"
            )
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(
            "Malformed registry row; fix the CSV before registering another candidate"
        )
    for row in rows:
        if row["video_id"] == video_id:
            return {
                "status": "already_registered",
                "event_id": row["event_id"],
                "video_id": video_id,
                "note": "Existing record preserved, including its manual decision",
            }
    numbers = [
        int(match.group(1))
        for row in rows
        if (match := re.fullmatch(r"candidate_(\d+)", row["event_id"]))
    ]
    event_id = f"candidate_{max(numbers, default=0) + 1:03d}"
    row = dict.fromkeys(fields, "")
    row.update(
        event_id=event_id,
        character_name=character.strip(),
        video_id=video_id,
        video_url=f"https://youtube.com/shorts/{video_id}",
        inclusion_status="pending",
    )
    # Append only: do not rewrite metadata, annotations or manual decisions already present.
    with path.open("rb") as stream:
        stream.seek(-1, 2)
        needs_newline = stream.read(1) not in {b"\n", b"\r"}
    with path.open("a", newline="", encoding="utf-8") as stream:
        if needs_newline:
            stream.write("\n")
        csv.DictWriter(stream, fieldnames=fields, lineterminator="\n").writerow(row)
    return {
        "status": "registered",
        "event_id": event_id,
        "video_id": video_id,
        "inclusion_status": "pending",
        "events_file": str(path),
        "note": "Link registered only; metadata and initial-drip classification are not yet verified",
    }
