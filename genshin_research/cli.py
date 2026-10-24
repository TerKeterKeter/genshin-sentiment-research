"""Argument definitions and dispatch for ``python -m genshin_research``."""

import argparse
import json
from datetime import datetime, timezone

from . import commands
from .core import read_json


def build_parser():
    parser = argparse.ArgumentParser(
        description="Offline-first Genshin research workflow"
    )
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--permissions", default="permissions.json")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="Audit registry and monthly data coverage")
    audit.add_argument("--events", default="templates/events.csv")
    audit.add_argument("--revenue", default="templates/revenue.csv")
    audit.add_argument("--coverage", default="templates/discovery_coverage.csv")
    audit.add_argument("--as-of", default=datetime.now(timezone.utc).date().isoformat())
    audit.set_defaults(handler=commands.run_audit)

    prepare = sub.add_parser(
        "prepare-audit", help="Create local CSVs without overwriting work"
    )
    prepare.add_argument("--destination", default="data")
    prepare.set_defaults(handler=commands.run_prepare_audit)

    revenue = sub.add_parser("revenue-check", help="Validate manual revenue imports")
    revenue.add_argument("--revenue", default="data/revenue.csv")
    revenue.set_defaults(handler=commands.run_revenue_check)

    metadata = sub.add_parser(
        "metadata", help="Verify video metadata and official channel"
    )
    metadata.add_argument("video_id")
    metadata.add_argument(
        "--refresh", action="store_true", help="Fetch fresh metadata (also the default)"
    )
    metadata.add_argument("--package")
    metadata.set_defaults(handler=commands.run_metadata)

    collect = sub.add_parser(
        "collect", help="Collect top-level comments with documented permission"
    )
    collect.add_argument("--events", required=True)
    collect.add_argument("--package", required=True)
    collect.set_defaults(handler=commands.run_collect)

    nlp = sub.add_parser(
        "nlp", help="Preprocess comments and run local sentiment inference"
    )
    nlp.add_argument("--package", required=True)
    nlp.set_defaults(handler=commands.run_nlp)

    annotate = sub.add_parser(
        "annotate", help="Sample comments for blind manual annotation"
    )
    annotate.add_argument("--package", required=True)
    annotate.add_argument("--events", required=True)
    annotate.set_defaults(handler=commands.run_annotate)

    evaluate = sub.add_parser(
        "evaluate", help="Evaluate predictions against manual labels"
    )
    evaluate.add_argument("--package", required=True)
    evaluate.set_defaults(handler=commands.run_evaluate)

    analyze = sub.add_parser(
        "analyze", help="Aggregate monthly sentiment and pair revenue at t+1"
    )
    analyze.add_argument("--package", required=True)
    analyze.add_argument("--events", required=True)
    analyze.add_argument("--revenue", required=True)
    analyze.set_defaults(handler=commands.run_analyze)

    pilot = sub.add_parser("pilot", help="Select verified events spread across time")
    pilot.add_argument("--events", required=True)
    pilot.set_defaults(handler=commands.run_pilot)

    purge = sub.add_parser(
        "purge", help="Delete an expired package or explicitly force deletion"
    )
    purge.add_argument("--package", required=True)
    purge.add_argument("--force", action="store_true")
    purge.set_defaults(handler=commands.run_purge)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    config = read_json(args.config)
    permissions = read_json(args.permissions)
    report = args.handler(args, config, permissions)
    if report is not None:
        print(json.dumps(report, indent=2))
