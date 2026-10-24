"""Purge entire data packages, including labels and derived artifacts."""
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .core import utc


def purge_package(package, now=None, force=False):
    package = Path(package).resolve()
    root = Path('data').resolve()
    if root not in package.parents or package == root:
        raise ValueError('Only packages strictly beneath ./data may be purged')
    manifest = json.loads((package / 'manifest.json').read_text())
    now = now or datetime.now(timezone.utc)
    expired = now >= utc(manifest['expires_at'])
    if force or expired:
        shutil.rmtree(package)
        return True
    return False


def refresh_metadata(api, video_id):
    # Refresh is authorized by the caller. It does not renew derived-data permission.
    return api.metadata(video_id)
