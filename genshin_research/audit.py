"""Validate a human-reviewed registry; never classify a video automatically."""

from collections import Counter
from datetime import date

from .core import utc

STATUSES = {"pending", "included", "excluded", "no_matching_short"}
REQUIRED_VERIFICATION = [
    "character_name",
    "announcement_source_url",
    "initial_announcement_at_utc",
    "video_id",
    "video_url",
    "channel_id",
    "video_published_at_utc",
    "verification_notes",
]


def audit(events, config, coverage):
    issues, accepted, seen_ids, seen_videos = [], [], set(), set()
    months = Counter()
    for row_number, event in enumerate(events, start=2):
        event_id = event.get("event_id", "")
        label = event_id or f"CSV row {row_number}"
        status = event.get("inclusion_status", "")
        if not event_id or event_id in seen_ids:
            issues.append(f"{label}: missing or duplicate event ID")
            continue
        seen_ids.add(event_id)
        if status not in STATUSES:
            issues.append(f"{label}: invalid inclusion_status")
            continue
        video_id = event.get("video_id")
        if video_id and video_id in seen_videos:
            issues.append(f"{label}: duplicate video ID")
            continue
        if video_id:
            seen_videos.add(video_id)
        if status in {"excluded", "no_matching_short"} and not event.get(
            "exclusion_reason"
        ):
            issues.append(f"{label}: exclusion_reason required")
        published = event.get("video_published_at_utc")
        try:
            if published:
                day = utc(published).date().isoformat()
                if (
                    not config["candidate_start"]
                    <= day
                    < config["candidate_end_exclusive"]
                ):
                    issues.append(f"{label}: outside candidate period")
                    continue
            if event.get("initial_announcement_at_utc"):
                utc(event["initial_announcement_at_utc"])
        except ValueError:
            issues.append(f"{label}: invalid timestamp; include timezone")
            continue
        if status != "included":
            continue
        if (
            any(not event.get(key) for key in REQUIRED_VERIFICATION)
            or event.get("content_type") != "verified_initial_drip_short"
        ):
            issues.append(f"{label}: incomplete manual/API verification")
            continue
        accepted.append(event_id)
        months[day[:7]] += 1

    discovery = {}
    for row in coverage:
        month = row.get("month", "")
        status = row.get("discovery_status", "")
        try:
            date.fromisoformat(month + "-01")
        except ValueError:
            issues.append(f"{month}: invalid discovery month")
            continue
        if (
            not config["candidate_start"][:7]
            <= month
            < config["candidate_end_exclusive"][:7]
        ):
            issues.append(f"{month}: discovery month outside candidate period")
            continue
        if month in discovery or status not in {"not_started", "partial", "completed"}:
            issues.append(f"{month}: duplicate month or invalid discovery status")
            continue
        discovery[month] = status
        if status == "completed" and not (
            row.get("checked_at_utc") and row.get("evidence_notes")
        ):
            issues.append(
                f"{month}: completed discovery needs timestamp and evidence notes"
            )
        if row.get("checked_at_utc"):
            try:
                utc(row["checked_at_utc"])
            except ValueError:
                issues.append(f"{month}: invalid discovery timestamp")
    required_months = []
    month = config["candidate_start"][:7]
    while month < config["candidate_end_exclusive"][:7]:
        required_months.append(month)
        year, number = map(int, month.split("-"))
        month = f"{year + (number == 12):04d}-{number % 12 + 1:02d}"
    return {
        "candidate_events": len(events),
        "included_verified_events": len(accepted),
        "events_by_publication_month": dict(sorted(months.items())),
        "events_by_publication_year": dict(
            Counter(month[:4] for month in months.elements())
        ),
        "pending_events": [
            e.get("event_id", "")
            for e in events
            if e.get("inclusion_status") == "pending"
        ],
        "without_suitable_short": [
            e.get("event_id", "")
            for e in events
            if e.get("inclusion_status") == "no_matching_short"
        ],
        "discovery_by_month": {
            month: discovery.get(month, "not_started") for month in required_months
        },
        "issues": issues,
        "note": "Included means recorded as verified by the researcher; the software does not verify video content. No verified event is not proof that no event exists.",
    }
