"""Read-only API verification; no comments or sentiment are requested."""

from datetime import datetime, timedelta, timezone

from .core import write_json
from .management import package_path


def verify_metadata(api, video_id):
    metadata = api.metadata(video_id)
    metadata["official_handle_channel_id"] = api.official_channel_id()
    metadata["matches_official_channel"] = (
        metadata["channel_id"] == metadata["official_handle_channel_id"]
    )
    return metadata


def save_metadata_package(metadata, package, retention_days):
    if type(retention_days) is not int or not 1 <= retention_days <= 30:
        raise ValueError("Metadata packages require retention of 1-30 days")
    package = package_path(package)
    package.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone.utc)
    manifest = {
        "verified_at_utc": now.isoformat(),
        "expires_at": (now + timedelta(days=retention_days)).isoformat(),
        "kind": "metadata_only",
        "synthetic": False,
    }
    write_json(package / "manifest.json", manifest)
    write_json(package / "metadata.json", metadata, ensure_ascii=False)
    return str(package)
