"""Command workflows. The CLI handles arguments and prints returned reports."""

import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from .aggregate import aggregate, explore, pair_revenue
from .audit import audit, choose_pilot, monthly_coverage
from .collector import YouTube, collect
from .core import authorize, read_csv, read_json, utc, write_csv, write_json
from .management import package_path, purge_package
from .metadata_audit import save_metadata_package, verify_metadata
from .nlp import annotation_sample, evaluate, infer, preprocess
from .preparation import prepare_audit, revenue_report


def require_complete_package(package):
    """Primary analysis requires unexpired data and completed pagination."""
    manifest = read_json(package / "manifest.json")
    if datetime.now(timezone.utc) >= utc(manifest["expires_at"]):
        raise ValueError("Package expired; purge or perform authorized re-collection")
    statuses = read_json(package / "collection_status.json")
    if not statuses or not all(s["pagination_complete"] for s in statuses):
        raise ValueError("Incomplete collection cannot enter primary analysis")


def run_prepare_audit(args, config, permissions):
    return prepare_audit(args.destination)


def run_revenue_check(args, config, permissions):
    return revenue_report(read_csv(args.revenue))


def run_audit(args, config, permissions):
    events, revenue = read_csv(args.events), read_csv(args.revenue)
    report = audit(events, revenue, config)
    report["calendar_coverage"] = monthly_coverage(
        events, revenue, config, read_csv(args.coverage), args.as_of
    )
    return report


def run_pilot(args, config, permissions):
    events = read_csv(args.events)
    report = audit(events, [], config)
    if report["issues"]:
        raise ValueError(report["issues"])
    return choose_pilot(events)


def run_purge(args, config, permissions):
    # Preserve the existing compact purge output for CLI compatibility.
    print({"purged": purge_package(args.package, force=args.force)})


def run_metadata(args, config, permissions):
    authorize(config, permissions, "metadata_allowed")
    api = YouTube(os.environ.get("YOUTUBE_API_KEY"))
    metadata = verify_metadata(api, args.video_id)
    if args.package:
        save_metadata_package(metadata, args.package, permissions["retention_days"])
    return metadata


def run_collect(args, config, permissions):
    authorize(config, permissions, "collection_allowed")
    package = package_path(args.package)
    events = read_csv(args.events)
    report = audit(events, [], config)
    if report["issues"] or not report["included_verified_events"]:
        raise ValueError("Resolve registry audit before collection: " + str(report))
    package.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone.utc)
    write_json(
        package / "manifest.json",
        {
            "collected_at": now.isoformat(),
            "expires_at": (
                now + timedelta(days=permissions["retention_days"])
            ).isoformat(),
            "permission_evidence": permissions["evidence_reference"],
            "synthetic": False,
        },
    )
    api = YouTube(os.environ.get("YOUTUBE_API_KEY"))
    official_id = api.official_channel_id()
    rows, statuses = [], []
    for event in events:
        if event["inclusion_status"] == "included":
            metadata = api.metadata(event["video_id"])
            if (
                metadata["channel_id"] != official_id
                or event["channel_id"] != official_id
            ):
                raise ValueError("Video is not from verified official channel")
            if utc(metadata["video_published_at_utc"]) != utc(
                event["video_published_at_utc"]
            ):
                raise ValueError("Registry publication timestamp differs from API")
            write_json(
                package
                / ("video_" + event["video_id"].replace("/", "_") + "_metadata.json"),
                metadata,
            )
            batch, status = collect(api, event, config["window_hours"])
            rows.extend(batch)
            statuses.append(status)
    if len({r["comment_id"] for r in rows}) != len(rows):
        raise ValueError("Repeated video/comment across registry events")
    write_csv(
        package / "comments.csv",
        rows,
        [
            "comment_id",
            "video_id",
            "event_id",
            "text_display",
            "published_at_utc",
            "updated_at_utc",
            "collected_at_utc",
            "like_count_at_collection",
            "language",
            "eligibility_status",
            "exclusion_reason",
        ],
    )
    write_json(package / "collection_status.json", statuses)
    return statuses


def run_nlp(args, config, permissions):
    authorize(config, permissions, "derived_analysis_allowed")
    package = package_path(args.package)
    require_complete_package(package)
    rows = preprocess(read_csv(package / "comments.csv"), config["language"])
    report = {
        "eligibility_counts": dict(Counter(r["eligibility_status"] for r in rows)),
        "exclusion_reasons": dict(
            Counter(
                (
                    r["exclusion_reason"]
                    for r in rows
                    if r["eligibility_status"] == "excluded"
                )
            )
        ),
        "excluded_languages": dict(
            Counter(
                (
                    r["language"]
                    for r in rows
                    if r["exclusion_reason"] == "non_english_or_undetermined"
                )
            )
        ),
    }
    write_json(package / "exclusions.json", report)
    write_csv(package / "predictions.csv", infer(rows, config))


def run_annotate(args, config, permissions):
    authorize(config, permissions, "derived_analysis_allowed")
    package = package_path(args.package)
    require_complete_package(package)
    if (package / "annotations.csv").exists():
        raise FileExistsError(
            "Preserve existing manual annotations; choose a new package or archive explicitly"
        )
    write_csv(
        package / "annotations.csv",
        annotation_sample(
            read_csv(package / "predictions.csv"),
            read_csv(args.events),
            seed=config["random_seed"],
        ),
    )


def run_evaluate(args, config, permissions):
    authorize(config, permissions, "derived_analysis_allowed")
    package = package_path(args.package)
    require_complete_package(package)
    predictions = {r["comment_id"]: r for r in read_csv(package / "predictions.csv")}
    annotations = read_csv(package / "annotations.csv")
    ids = [r["comment_id"] for r in annotations]
    if len(ids) != len(set(ids)) or any(cid not in predictions for cid in ids):
        raise ValueError("Annotations must have unique IDs matching predictions")
    labeled = [
        {**r, "sentiment": predictions[r["comment_id"]].get("sentiment", "")}
        for r in annotations
    ]
    return evaluate(labeled)


def run_analyze(args, config, permissions):
    authorize(config, permissions, "derived_analysis_allowed")
    package = package_path(args.package)
    require_complete_package(package)
    authorize(config, permissions, "external_join_allowed")
    events = read_csv(args.events)
    revenue = read_csv(args.revenue)
    report = audit(events, revenue, config)
    if report["issues"]:
        raise ValueError(report["issues"])
    monthly = aggregate(
        events, read_csv(package / "predictions.csv"), config["window_hours"]
    )
    write_csv(package / "monthly.csv", monthly)
    pairs = pair_revenue(monthly, revenue)
    write_csv(package / "pairs.csv", pairs)
    return explore(pairs, package / "scatter.png")
