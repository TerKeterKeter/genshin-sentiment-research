"""Local audit preparation. No credentials, network requests or research results."""
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
from math import isfinite
from .core import utc

TEMPLATES = ['events.csv', 'discovery_coverage.csv', 'revenue.csv']


def prepare_audit(destination='data', templates='templates'):
    destination = Path(destination).resolve()
    root = Path('data').resolve()
    if destination != root and root not in destination.parents:
        raise ValueError('Audit working files must stay within ./data (ignored by Git)')
    destination.mkdir(parents=True, exist_ok=True)
    result = {'created': [], 'preserved': []}
    for filename in TEMPLATES:
        target = destination / filename
        if target.exists():
            result['preserved'].append(str(target))
            continue
        # Exclusive creation also protects against accidental concurrent overwrites.
        contents = (Path(templates) / filename).read_text(encoding='utf-8')
        with target.open('x', encoding='utf-8', newline='') as stream:
            stream.write(contents)
        result['created'].append(str(target))
    return result


def validate_revenue_rows(rows):
    """Validate CSV syntax/provenance fields; cannot authenticate the source."""
    required = ['month', 'revenue_usd', 'platform_scope', 'region_scope',
                'cn_android_included', 'cn_android_multiplier', 'source_url',
                'retrieved_at', 'revision_notes']
    for number, row in enumerate(rows, start=2):
        if any(field not in row or row[field] is None for field in required):
            raise ValueError(f'Revenue CSV row {number}: missing required columns or cells')
        try:
            date.fromisoformat(row['month'] + '-01')
        except ValueError:
            raise ValueError(f'Revenue CSV row {number}: month must be YYYY-MM') from None
        if row['cn_android_included'] not in {'true', 'false', 'unknown'}:
            raise ValueError(f'Revenue CSV row {number}: cn_android_included must be true, false or unknown')
        multiplier = row['cn_android_multiplier']
        if multiplier:
            try:
                value = float(multiplier)
            except ValueError:
                raise ValueError(f'Revenue CSV row {number}: invalid CN Android multiplier') from None
            if not isfinite(value) or value <= 0 or row['cn_android_included'] != 'true':
                raise ValueError(f'Revenue CSV row {number}: multiplier requires included=true and a finite positive number')
        url = urlsplit(row['source_url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError(f'Revenue CSV row {number}: use a public HTTPS source URL without credentials')
        try:
            if 'T' in row['retrieved_at']:
                utc(row['retrieved_at'])
            else:
                date.fromisoformat(row['retrieved_at'])
        except ValueError:
            raise ValueError(f'Revenue CSV row {number}: retrieved_at must be an ISO date or timezone-aware timestamp') from None


def revenue_report(rows):
    from .aggregate import pair_revenue
    pair_revenue([], rows)
    missing = sorted(r['month'] for r in rows if r['revenue_usd'] == '')
    unknown = sorted(r['month'] for r in rows if r['cn_android_included'] == 'unknown')
    return {'status': 'empty' if not rows else 'valid_format_requires_source_review',
            'row_count': len(rows), 'available_months': sorted(r['month'] for r in rows if r['revenue_usd'] != ''),
            'missing_value_months': missing, 'unknown_cn_android_months': unknown,
            'source_verified': False,
            'note': 'Format checks cannot confirm actual values, coverage consistency or usage rights; manual source review required.'}
