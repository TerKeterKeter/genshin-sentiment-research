from collections import defaultdict
from datetime import timedelta
import math
from .core import utc


def aggregate(events, comments, hours=72):
    months = defaultdict(lambda: {'events': set(), 'comments': []})
    event_month = {}
    for e in events:
        if e['inclusion_status'] != 'included':
            continue
        month = (utc(e['video_published_at_utc']) + timedelta(hours=hours)).strftime('%Y-%m')
        event_month[e['event_id']] = month
        months[month]['events'].add(e['event_id'])
    seen = set()
    for row in comments:
        if row['comment_id'] in seen:
            raise ValueError('Duplicate comment ID in analysis input')
        seen.add(row['comment_id'])
        if row['eligibility_status'] == 'eligible' and row.get('sentiment') in {'positive','negative','neutral'}:
            months[event_month[row['event_id']]]['comments'].append(row)
    result = []
    for month, group in sorted(months.items()):
        n = len(group['comments'])
        row = dict(month=month, event_count=len(group['events']), comment_count=n)
        for label in ['positive','negative','neutral']:
            row[label+'_proportion'] = sum(r['sentiment'] == label for r in group['comments']) / n if n else None
        row['net_sentiment'] = row['positive_proportion'] - row['negative_proportion'] if n else None
        result.append(row)
    return result


def pair_revenue(monthly, revenue):
    scopes, sources, lookup = set(), set(), {}
    for row in revenue:
        required = ['month', 'platform_scope', 'region_scope', 'cn_android_included', 'source_url', 'retrieved_at']
        if any(not row.get(key) for key in required):
            raise ValueError('Revenue provenance and coverage fields required')
        from datetime import datetime
        if datetime.strptime(row['month'], '%Y-%m').strftime('%Y-%m') != row['month']:
            raise ValueError('Revenue month must be YYYY-MM')
        sources.add(row['source_url'])
        if row['month'] in lookup:
            raise ValueError('Duplicate revenue month; choose one revision')
        scopes.add(tuple(row[k] for k in ['platform_scope','region_scope','cn_android_included','cn_android_multiplier']))
        if row['revenue_usd']:
            value = float(row['revenue_usd'])
            if not math.isfinite(value) or value < 0:
                raise ValueError('Invalid revenue value')
        lookup[row['month']] = row
    if len(sources) > 1:
        raise ValueError('Use one documented revenue source series')
    if len(scopes) > 1:
        raise ValueError('Revenue coverage differs across rows')
    pairs = []
    for row in monthly:
        y, m = map(int, row['month'].split('-'))
        next_month = f'{y + (m == 12):04d}-{m % 12 + 1:02d}'
        rev = lookup.get(next_month)
        if row['net_sentiment'] is not None and rev and rev['revenue_usd']:
            pairs.append({**row, 'revenue_month': next_month, 'revenue_usd': float(rev['revenue_usd'])})
    return pairs


def explore(pairs, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.stats import spearmanr
    x, y = [r['net_sentiment'] for r in pairs], [r['revenue_usd'] for r in pairs]
    if len(pairs) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        raise ValueError('At least three nonconstant monthly pairs needed; this is not a power criterion')
    rho, p = spearmanr(x, y)
    fig, ax = plt.subplots()
    ax.scatter(x, y)
    for row in pairs:
        ax.annotate(row['month'], (row['net_sentiment'], row['revenue_usd']))
    ax.set(xlabel='Net sentiment, window-end month t', ylabel='Estimated mobile revenue USD, t+1')
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return {'actual_pairs': len(pairs), 'spearman_rho': float(rho), 'p_value_exploratory': float(p),
            'forecasting': 'deferred; assess month count, missingness and information available before prediction'}
