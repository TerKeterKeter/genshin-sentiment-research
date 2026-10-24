import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
from .core import read_csv, write_csv, authorize, utc
from .audit import audit, choose_pilot
from .collector import YouTube, collect
from .nlp import preprocess, infer, annotation_sample, evaluate
from .aggregate import aggregate, pair_revenue, explore
from .management import purge_package, refresh_metadata


def main():
    parser = argparse.ArgumentParser(description='Offline-first Genshin research workflow')
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--permissions', default='permissions.json')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('audit'); p.add_argument('--events', default='templates/events.csv'); p.add_argument('--revenue', default='templates/revenue.csv')
    p = sub.add_parser('metadata'); p.add_argument('video_id'); p.add_argument('--refresh', action='store_true')
    p = sub.add_parser('collect'); p.add_argument('--events', required=True); p.add_argument('--package', required=True)
    p = sub.add_parser('nlp'); p.add_argument('--package', required=True)
    p = sub.add_parser('annotate'); p.add_argument('--package', required=True); p.add_argument('--events', required=True)
    p = sub.add_parser('evaluate'); p.add_argument('--package', required=True)
    p = sub.add_parser('analyze'); p.add_argument('--package', required=True); p.add_argument('--events', required=True); p.add_argument('--revenue', required=True)
    p = sub.add_parser('pilot'); p.add_argument('--events', required=True)
    p = sub.add_parser('purge'); p.add_argument('--package', required=True); p.add_argument('--force', action='store_true')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    permissions = json.loads(Path(args.permissions).read_text())
    if args.command == 'audit':
        print(json.dumps(audit(read_csv(args.events), read_csv(args.revenue), config), indent=2)); return
    if args.command == 'pilot':
        events = read_csv(args.events)
        report = audit(events, [], config)
        if report['issues']:
            raise ValueError(report['issues'])
        print(json.dumps(choose_pilot(events), indent=2)); return
    if args.command == 'purge':
        print({'purged': purge_package(args.package, force=args.force)}); return
    if args.command == 'metadata':
        authorize(config, permissions, 'collection_allowed')
        api = YouTube(os.environ.get('YOUTUBE_API_KEY'))
        metadata = refresh_metadata(api, args.video_id) if args.refresh else api.metadata(args.video_id)
        metadata['official_handle_channel_id'] = api.official_channel_id()
        metadata['matches_official_channel'] = metadata['channel_id'] == metadata['official_handle_channel_id']
        print(json.dumps(metadata, indent=2)); return
    authorize(config, permissions, 'collection_allowed' if args.command == 'collect' else 'derived_analysis_allowed')
    package = Path(args.package).resolve()
    if Path('data').resolve() not in package.parents:
        raise ValueError('Packages must live beneath ./data')
    if args.command == 'collect':
        events = read_csv(args.events)
        report = audit(events, [], config)
        if report['issues'] or not report['included_verified_events']:
            raise ValueError('Resolve registry audit before collection: ' + str(report))
        # A new package avoids overwriting user data or extending old retention dates.
        package.mkdir(parents=True, exist_ok=False)
        now = datetime.now(timezone.utc)
        (package / 'manifest.json').write_text(json.dumps({'collected_at': now.isoformat(),
            'expires_at': (now + timedelta(days=permissions['retention_days'])).isoformat(),
            'permission_evidence': permissions['evidence_reference'], 'synthetic': False}, indent=2))
        api = YouTube(os.environ.get('YOUTUBE_API_KEY'))
        official_id = api.official_channel_id()
        rows, statuses = [], []
        for event in events:
            if event['inclusion_status'] == 'included':
                metadata = api.metadata(event['video_id'])
                if metadata['channel_id'] != official_id or event['channel_id'] != official_id:
                    raise ValueError('Video is not from verified official channel')
                if utc(metadata['video_published_at_utc']) != utc(event['video_published_at_utc']):
                    raise ValueError('Registry publication timestamp differs from API')
                (package / ('video_' + event['video_id'].replace('/', '_') + '_metadata.json')).write_text(json.dumps(metadata, indent=2))
                batch, status = collect(api, event, config['window_hours'])
                rows.extend(batch); statuses.append(status)
        if len({r['comment_id'] for r in rows}) != len(rows):
            raise ValueError('Repeated video/comment across registry events')
        write_csv(package / 'comments.csv', rows, ['comment_id','video_id','event_id','text_display','published_at_utc','updated_at_utc','collected_at_utc','like_count_at_collection','language','eligibility_status','exclusion_reason'])
        (package / 'collection_status.json').write_text(json.dumps(statuses, indent=2))
        print(json.dumps(statuses, indent=2)); return
    manifest = json.loads((package / 'manifest.json').read_text())
    if datetime.now(timezone.utc) >= utc(manifest['expires_at']):
        raise ValueError('Package expired; purge or perform authorized re-collection')
    statuses = json.loads((package / 'collection_status.json').read_text())
    if not statuses or not all(s['pagination_complete'] for s in statuses):
        raise ValueError('Incomplete collection cannot enter primary analysis')
    if args.command == 'nlp':
        rows = preprocess(read_csv(package / 'comments.csv'), config['language'])
        report = {'eligibility_counts': dict(Counter(r['eligibility_status'] for r in rows)),
                  'exclusion_reasons': dict(Counter(r['exclusion_reason'] for r in rows if r['eligibility_status'] == 'excluded')),
                  'excluded_languages': dict(Counter(r['language'] for r in rows if r['exclusion_reason'] == 'non_english_or_undetermined'))}
        (package / 'exclusions.json').write_text(json.dumps(report, indent=2))
        write_csv(package / 'predictions.csv', infer(rows, config))
    elif args.command == 'annotate':
        if (package / 'annotations.csv').exists():
            raise FileExistsError('Preserve existing manual annotations; choose a new package or archive explicitly')
        write_csv(package / 'annotations.csv', annotation_sample(read_csv(package / 'predictions.csv'), read_csv(args.events), seed=config['random_seed']))
    elif args.command == 'evaluate':
        predictions = {r['comment_id']: r for r in read_csv(package / 'predictions.csv')}
        annotations = read_csv(package / 'annotations.csv')
        ids = [r['comment_id'] for r in annotations]
        if len(ids) != len(set(ids)) or any(cid not in predictions for cid in ids):
            raise ValueError('Annotations must have unique IDs matching predictions')
        labeled = [{**r, 'sentiment': predictions[r['comment_id']].get('sentiment', '')} for r in annotations]
        print(json.dumps(evaluate(labeled), indent=2))
    elif args.command == 'analyze':
        authorize(config, permissions, 'external_join_allowed')
        events = read_csv(args.events)
        report = audit(events, read_csv(args.revenue), config)
        if report['issues']:
            raise ValueError(report['issues'])
        monthly = aggregate(events, read_csv(package / 'predictions.csv'), config['window_hours'])
        write_csv(package / 'monthly.csv', monthly)
        pairs = pair_revenue(monthly, read_csv(args.revenue))
        write_csv(package / 'pairs.csv', pairs)
        print(json.dumps(explore(pairs, package / 'scatter.png'), indent=2))


if __name__ == '__main__':
    main()
