"""All comments, identifiers and economic numbers here are SYNTHETIC TEST DATA."""
import unittest
from genshin_research.collector import collect
from genshin_research.core import eligibility, authorize
from genshin_research.audit import audit
from genshin_research.aggregate import aggregate, pair_revenue

START = '2024-01-29T00:00:00Z'
EVENT = dict(event_id='SYNTHETIC', video_id='TEST', video_published_at_utc=START, inclusion_status='included')


def item(cid, published=START, updated=START):
    return {'snippet': {'topLevelComment': {'id': cid, 'snippet': {
        'textDisplay': 'SYNTHETIC TEST COMMENT', 'publishedAt': published,
        'updatedAt': updated, 'likeCount': 3}}}}


class OfflineTests(unittest.TestCase):
    def test_pagination_dedup(self):
        calls = []
        def api(resource, params):
            calls.append(params)
            if 'pageToken' not in params:
                return {'items': [item('a')], 'nextPageToken': 'second'}
            return {'items': [item('a'), item('b')]}
        rows, status = collect(api, EVENT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(status['duplicate_ids'], 1)
        self.assertTrue(status['pagination_complete'])
        self.assertEqual(calls[1]['pageToken'], 'second')
        self.assertEqual(calls[0]['maxResults'], 100)
        self.assertEqual(calls[0]['order'], 'time')
        self.assertEqual(calls[0]['textFormat'], 'plainText')
        self.assertNotIn('author', str(rows))

    def test_timestamp_boundaries(self):
        for published, expected in [(START, 'eligible'), ('2024-01-31T23:59:59Z', 'eligible'),
              ('2024-02-01T00:00:00Z', 'excluded'), ('2024-01-28T23:59:59Z', 'excluded')]:
            self.assertEqual(eligibility(published, published, START)[0], expected)

    def test_edit_after_cutoff(self):
        self.assertEqual(eligibility(START, '2024-02-01T00:00:01Z', START),
                         ('excluded', 'edited_at_or_after_cutoff'))

    def test_interrupted_collection(self):
        def api(resource, params):
            if 'pageToken' in params:
                raise RuntimeError('synthetic interruption')
            return {'items': [item('a')], 'nextPageToken': 'next'}
        rows, status = collect(api, EVENT)
        self.assertEqual(len(rows), 1)
        self.assertFalse(status['pagination_complete'])
        self.assertEqual(status['error'], 'synthetic interruption')

    def test_month_assignment_and_missing(self):
        rows = [dict(comment_id='a', event_id='SYNTHETIC', eligibility_status='eligible', sentiment='positive')]
        monthly = aggregate([EVENT], rows)
        self.assertEqual(monthly[0]['month'], '2024-02')
        self.assertEqual(monthly[0]['net_sentiment'], 1)
        self.assertEqual(pair_revenue(monthly, []), [])
        self.assertIsNone(aggregate([EVENT], [])[0]['net_sentiment'])

    def test_permission_gate(self):
        with self.assertRaises(PermissionError):
            authorize({'dry_run': True}, {}, 'collection_allowed')
        with self.assertRaises(PermissionError):
            authorize({'dry_run': False}, {}, 'derived_analysis_allowed')

    def test_empty_audit(self):
        report = audit([], [], {'window_hours':72})
        self.assertEqual(report['potential_pair_count'], 0)
        self.assertEqual(report['included_verified_events'], 0)


if __name__ == '__main__':
    unittest.main()
