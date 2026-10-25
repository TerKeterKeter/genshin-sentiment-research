"""Purge entire data packages, including labels and derived artifacts."""

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .core import read_json, utc


def purge_package(package, now=None, force=False):
    package = package_path(package)
    manifest = read_json(package / "manifest.json")
    now = now or datetime.now(timezone.utc)
    expired = now >= utc(manifest["expires_at"])
    if force or expired:
        shutil.rmtree(package)
        return True
    return False


def package_path(package):
    """Resolve a package strictly beneath the local, ignored data directory."""
    package = Path(package).resolve()
    if Path("data").resolve() not in package.parents:
        raise ValueError("Packages must live beneath ./data")
    return package
