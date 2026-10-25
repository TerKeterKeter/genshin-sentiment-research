"""Small CLI for the current manual-verification stage."""

import argparse
import json
import os

from .audit import audit
from .core import authorize, read_csv, read_json
from .management import purge_package
from .metadata_audit import save_metadata_package, verify_metadata
from .preparation import prepare_audit
from .registry import register_candidate
from .youtube import YouTube


def build_parser():
    parser = argparse.ArgumentParser(
        description="Prepare and manually verify Genshin event candidates"
    )
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--permissions", default="permissions.json")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser(
        "prepare-audit", help="Create local registry and discovery CSVs"
    )
    prepare.add_argument("--destination", default="data")
    register = sub.add_parser(
        "register", help="Register a candidate Short link offline"
    )
    register.add_argument("video", help="HTTPS Shorts link or video ID")
    register.add_argument("--character", default="")
    register.add_argument("--events", default="data/events.csv")
    metadata = sub.add_parser(
        "metadata", help="Read video/channel metadata, without classifying content"
    )
    metadata.add_argument("video_id")
    metadata.add_argument("--package")
    review = sub.add_parser(
        "audit", help="Check manual registry and discovery completeness"
    )
    review.add_argument("--events", default="data/events.csv")
    review.add_argument("--coverage", default="data/discovery_coverage.csv")
    serve = sub.add_parser("serve", help="Open the local browser workbench")
    serve.add_argument("--port", type=int, default=5000)
    serve.add_argument("--data-dir", default="data/workbench")
    purge = sub.add_parser("purge", help="Delete an expired local package")
    purge.add_argument("--package", required=True)
    purge.add_argument("--force", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        from .web import create_app

        create_app(args.data_dir).run(
            host="127.0.0.1", port=args.port, debug=False, use_reloader=False
        )
        return
    if args.command == "prepare-audit":
        report = prepare_audit(args.destination)
    elif args.command == "register":
        report = register_candidate(args.video, args.events, args.character)
    elif args.command == "purge":
        report = {"purged": purge_package(args.package, force=args.force)}
    elif args.command == "audit":
        config = read_json(args.config)
        report = audit(read_csv(args.events), config, read_csv(args.coverage))
    elif args.command == "metadata":
        config = read_json(args.config)
        permissions = read_json(args.permissions)
        authorize(config, permissions, "metadata_allowed")
        api = YouTube(os.environ.get("YOUTUBE_API_KEY"))
        report = verify_metadata(api, args.video_id)
        if args.package:
            save_metadata_package(report, args.package, permissions["retention_days"])
    print(json.dumps(report, indent=2))
