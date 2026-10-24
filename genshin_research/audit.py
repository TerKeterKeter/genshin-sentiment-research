from collections import Counter
from datetime import date, timedelta

from .core import next_month, utc


def audit(events, revenue, config):
    accepted, issues, months = [], [], Counter()
    publication_months = Counter()
    seen, seen_videos = set(), set()
    for event in events:
        eid = event["event_id"]
        if eid in seen:
            issues.append(f"{eid}: duplicate event ID")
            continue
        seen.add(eid)
        video_id = event.get("video_id")
        if video_id and video_id in seen_videos:
            issues.append(
                f"{eid}: duplicate video ID; do not count one Short as independent events"
            )
            continue
        if video_id:
            seen_videos.add(video_id)
        if event["inclusion_status"] != "included":
            continue
        required = [
            "character_name",
            "announcement_source_url",
            "initial_announcement_at_utc",
            "video_id",
            "video_url",
            "channel_id",
            "video_published_at_utc",
            "verification_notes",
        ]
        if (
            any(not event.get(key) for key in required)
            or event["content_type"] != "verified_initial_drip_short"
        ):
            issues.append(f"{eid}: incomplete manual/API verification")
            continue
        try:
            day = utc(event["video_published_at_utc"]).date().isoformat()
            utc(event["initial_announcement_at_utc"])
            if not config["candidate_start"] <= day < config["candidate_end_exclusive"]:
                issues.append(f"{eid}: outside candidate period")
                continue
            month = (
                utc(event["video_published_at_utc"])
                + timedelta(hours=config["window_hours"])
            ).strftime("%Y-%m")
        except ValueError:
            issues.append(f"{eid}: invalid timestamp")
            continue
        publication_months[day[:7]] += 1
        accepted.append(eid)
        months[month] += 1
    available = {row["month"] for row in revenue if row.get("revenue_usd")}
    paired = [month for month in months if next_month(month) in available]
    return {
        "candidate_events": len(events),
        "included_verified_events": len(accepted),
        "events_by_window_end_month": dict(sorted(months.items())),
        "events_by_publication_month": dict(sorted(publication_months.items())),
        "events_by_publication_year": dict(
            Counter(m[:4] for m in publication_months.elements())
        ),
        "without_suitable_short": [
            e["event_id"]
            for e in events
            if e["inclusion_status"] == "no_matching_short"
        ],
        "pending_events": [
            e["event_id"] for e in events if e["inclusion_status"] == "pending"
        ],
        "revenue_months_available": sorted(available),
        "potential_paired_months": paired,
        "potential_pair_count": len(paired),
        "issues": issues,
        "feasibility": "not_established; requires complete registry, permission, collection and validated revenue",
    }


def choose_pilot(events, n=8):
    """Evenly spaced temporal selection; no sentiment or revenue selection."""
    valid = sorted(
        [e for e in events if e["inclusion_status"] == "included"],
        key=lambda e: utc(e["video_published_at_utc"]),
    )
    if len(valid) < 6:
        raise ValueError("At least six verified eligible events required")
    n = min(max(n, 6), 10, len(valid))
    return [valid[round(i * (len(valid) - 1) / (n - 1))] for i in range(n)]


def monthly_coverage(events, revenue, config, coverage, as_of):
    """Calendar audit, including unknown/no-event and unfinished revenue months."""
    from .aggregate import pair_revenue

    day = date.fromisoformat(as_of)
    # Reuse source/scope/value validation without manufacturing observations.
    pair_revenue([], revenue)
    report = audit(events, revenue, config)
    if report["issues"]:
        raise ValueError(report["issues"])
    discovery = {}
    for row in coverage:
        month = row["month"]
        if month in discovery:
            raise ValueError("Duplicate discovery month")
        if row["discovery_status"] not in {"not_started", "partial", "completed"}:
            raise ValueError("Invalid discovery status")
        if row["discovery_status"] == "completed" and not (
            row["checked_at_utc"] and row["evidence_notes"]
        ):
            raise ValueError("Completed discovery needs timestamp and evidence notes")
        if row.get("checked_at_utc"):
            utc(row["checked_at_utc"])
        discovery[month] = row["discovery_status"]
    start = config["candidate_start"][:7]
    end = config["candidate_end_exclusive"]
    last_publication = (utc(end + "T00:00:00Z") - timedelta(microseconds=1)).strftime(
        "%Y-%m"
    )
    last_window = (
        utc(end + "T00:00:00Z")
        + timedelta(hours=config["window_hours"])
        - timedelta(microseconds=1)
    ).strftime("%Y-%m")
    available = {r["month"] for r in revenue if r["revenue_usd"] != ""}
    result = []
    month = start
    while month <= last_window:
        revenue_month = next_month(month)
        complete = date.fromisoformat(next_month(revenue_month) + "-01") <= day
        n = report["events_by_window_end_month"].get(month, 0)
        discovery_status = (
            discovery.get(month, "not_started")
            if month <= last_publication
            else "outside_publication_period"
        )
        if revenue_month in available:
            revenue_status = (
                "available" if complete else "provided_but_month_incomplete"
            )
        else:
            revenue_status = (
                "missing_or_not_imported" if complete else "month_not_complete"
            )
        # Window-end month can also receive events published in the prior month.
        result.append(
            {
                "window_end_month": month,
                "verified_event_count": n,
                "publication_discovery_status": discovery_status,
                "window_month_status": "verified_events_present"
                if n
                else "no_verified_events_yet",
                "revenue_month": revenue_month,
                "revenue_status": revenue_status,
                "potential_pair": bool(n and revenue_status == "available"),
            }
        )
        month = next_month(month)
    return {
        "as_of": as_of,
        "months": result,
        "potential_pair_count": sum(r["potential_pair"] for r in result),
        "actual_pair_count": None,
        "note": "Discovery tracks publication months; window-end months may include prior-month events. "
        "No verified events yet does not mean no events exist. Actual pairs require eligible "
        "comments and evaluated sentiment; not computed during registry audit.",
    }
