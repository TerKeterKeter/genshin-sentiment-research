from collections import Counter
from datetime import timedelta
from .core import utc


def audit(events, revenue, config):
    accepted, issues, months = [], [], Counter()
    publication_months = Counter()
    seen, seen_videos = set(), set()
    for event in events:
        eid = event['event_id']
        if eid in seen:
            issues.append(f'{eid}: duplicate event ID')
            continue
        seen.add(eid)
        video_id = event.get('video_id')
        if video_id and video_id in seen_videos:
            issues.append(f'{eid}: duplicate video ID; do not count one Short as independent events')
            continue
        if video_id:
            seen_videos.add(video_id)
        if event['inclusion_status'] != 'included':
            continue
        required = ['character_name', 'announcement_source_url', 'initial_announcement_at_utc',
                    'video_id', 'video_url', 'channel_id', 'video_published_at_utc', 'verification_notes']
        if any(not event.get(key) for key in required) or event['content_type'] != 'verified_initial_drip_short':
            issues.append(f'{eid}: incomplete manual/API verification')
            continue
        try:
            day = utc(event['video_published_at_utc']).date().isoformat()
            utc(event['initial_announcement_at_utc'])
            if not config['candidate_start'] <= day < config['candidate_end_exclusive']:
                issues.append(f'{eid}: outside candidate period')
                continue
            month = (utc(event['video_published_at_utc']) + timedelta(hours=config['window_hours'])).strftime('%Y-%m')
        except ValueError:
            issues.append(f'{eid}: invalid timestamp')
            continue
        publication_months[day[:7]] += 1
        accepted.append(eid)
        months[month] += 1
    available = {row['month'] for row in revenue if row.get('revenue_usd')}
    def following(month):
        y, m = map(int, month.split('-'))
        return f'{y + (m == 12):04d}-{m % 12 + 1:02d}'
    paired = [month for month in months if following(month) in available]
    return {'candidate_events': len(events), 'included_verified_events': len(accepted),
            'events_by_window_end_month': dict(sorted(months.items())),
            'events_by_publication_month': dict(sorted(publication_months.items())),
            'events_by_publication_year': dict(Counter(m[:4] for m in publication_months.elements())),
            'without_suitable_short': [e['event_id'] for e in events if e['inclusion_status'] == 'no_matching_short'],
            'pending_events': [e['event_id'] for e in events if e['inclusion_status'] == 'pending'],
            'revenue_months_available': sorted(available), 'potential_paired_months': paired,
            'potential_pair_count': len(paired), 'issues': issues,
            'feasibility': 'not_established; requires complete registry, permission, collection and validated revenue'}


def choose_pilot(events, n=8):
    """Evenly spaced temporal selection; no sentiment or revenue selection."""
    valid = sorted([e for e in events if e['inclusion_status'] == 'included'],
                   key=lambda e: utc(e['video_published_at_utc']))
    if len(valid) < 6:
        raise ValueError('At least six verified eligible events required')
    n = min(max(n, 6), 10, len(valid))
    return [valid[round(i * (len(valid)-1)/(n-1))] for i in range(n)]
