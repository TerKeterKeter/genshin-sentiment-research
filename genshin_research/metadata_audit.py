"""Read-only API verification; no comments or sentiment are requested."""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta


def verify_metadata(api, video_id):
    metadata = api.metadata(video_id)
    metadata['official_handle_channel_id'] = api.official_channel_id()
    metadata['matches_official_channel'] = metadata['channel_id'] == metadata['official_handle_channel_id']
    return metadata


def save_metadata_package(metadata, package, retention_days):
    if type(retention_days) is not int or not 1 <= retention_days <= 30:
        raise ValueError('Metadata packages require retention of 1-30 days')
    package = Path(package).resolve()
    if Path('data').resolve() not in package.parents:
        raise ValueError('Metadata packages must be strictly beneath ./data')
    package.mkdir(parents=True, exist_ok=False)
    now = datetime.now(timezone.utc)
    manifest = {'verified_at_utc': now.isoformat(),
                'expires_at': (now + timedelta(days=retention_days)).isoformat(),
                'kind': 'metadata_only', 'synthetic': False}
    (package / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (package / 'metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return str(package)
