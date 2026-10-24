"""SYNTHETIC fixtures only: no real comments or revenue."""
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from genshin_research.core import write_csv, read_csv
from genshin_research.aggregate import aggregate, pair_revenue
from genshin_research.nlp import annotation_sample, normalize
from genshin_research.management import purge_package


class WorkflowTests(unittest.TestCase):
    def test_union_csv_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.csv'
            write_csv(path, [{'id':'a'}, {'id':'b', 'score':'.9'}])
            self.assertEqual(read_csv(path)[1]['score'], '.9')

    def test_preserve_negation_emoji(self):
        self.assertEqual(normalize('  not   bad 😄\n'), 'not bad 😄')

    def test_stratified_sample_reproducible(self):
        events = [dict(event_id='TEST', video_published_at_utc='2024-01-01T00:00:00Z')]
        rows = [dict(comment_id=str(i), event_id='TEST', published_at_utc=f'2024-01-0{1+i%3}T01:00:00Z', eligibility_status='eligible') for i in range(30)]
        first = annotation_sample(rows, events, n=9)
        self.assertEqual(first, annotation_sample(list(reversed(rows)), events, n=9))
        self.assertEqual({r['interval_24h'] for r in first}, {0,1,2})
        self.assertEqual(len({r['comment_id'] for r in first}), 9)

    def test_revenue_pair_lag_and_scope(self):
        monthly = [dict(month='2024-12', net_sentiment=.2)]
        revenue = [dict(month='2025-01', revenue_usd='100', platform_scope='SYNTHETIC_MOBILE',region_scope='TEST',cn_android_included='false',cn_android_multiplier='',source_url='https://example.invalid/SYNTHETIC',retrieved_at='2025-02-01',revision_notes='TEST')]
        self.assertEqual(pair_revenue(monthly, revenue)[0]['revenue_month'], '2025-01')
        with self.assertRaises(ValueError):
            pair_revenue(monthly, revenue + revenue)
        with self.assertRaises(ValueError):
            pair_revenue(monthly, revenue + [{**revenue[0], 'month':'2025-02','region_scope':'different'}])

    def test_purge_expiry_and_path_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            import os
            old = os.getcwd()
            try:
                os.chdir(folder)
                package = Path('data/test'); package.mkdir(parents=True)
                (package / 'manifest.json').write_text(json.dumps({'expires_at':'2024-01-02T00:00:00Z'}))
                (package / 'derived.csv').write_text('SYNTHETIC')
                self.assertFalse(purge_package(package, now=datetime(2024,1,1,tzinfo=timezone.utc)))
                self.assertTrue(purge_package(package, now=datetime(2024,1,3,tzinfo=timezone.utc)))
                self.assertFalse(package.exists())
                with self.assertRaises(ValueError):
                    purge_package(Path(folder), force=True)
            finally:
                os.chdir(old)

@unittest.skipUnless(__import__('importlib.util').util.find_spec('requests'), 'HTTP adapter tests require requests; core offline tests do not')
class TransportTests(unittest.TestCase):
    def test_retry_limited_then_success(self):
        from unittest.mock import patch, Mock
        from genshin_research.collector import YouTube
        responses = [Mock(status_code=429), Mock(status_code=200)]
        responses[1].json.return_value = {'items': []}
        with patch('requests.get', side_effect=responses) as request, patch('time.sleep'):
            self.assertEqual(YouTube('SYNTHETIC_KEY')('videos', {}), {'items': []})
            self.assertEqual(request.call_count, 2)

    def test_permission_error_not_retried(self):
        from unittest.mock import patch, Mock
        from genshin_research.collector import YouTube
        with patch('requests.get', return_value=Mock(status_code=403)) as request:
            with self.assertRaisesRegex(RuntimeError, 'HTTP 403'):
                YouTube('SYNTHETIC_KEY')('videos', {})
            self.assertEqual(request.call_count, 1)
