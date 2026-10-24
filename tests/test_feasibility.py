"""SYNTHETIC fixtures only; no API calls or empirical revenue."""
import unittest
from genshin_research.audit import monthly_coverage, audit
from genshin_research.core import authorize

CONFIG = {'candidate_start':'2026-01-01','candidate_end_exclusive':'2026-10-01','window_hours':72,'dry_run':True}


def event(timestamp):
    return dict(event_id='SYNTHETIC', character_name='TEST', announcement_source_url='https://example.invalid/TEST',
                initial_announcement_at_utc=timestamp, video_id='TEST', video_url='https://example.invalid/TEST',
                channel_id='TEST', video_published_at_utc=timestamp, content_type='verified_initial_drip_short',
                inclusion_status='included', verification_notes='SYNTHETIC TEST VERIFICATION')


class FeasibilityTests(unittest.TestCase):
    def test_no_events_does_not_mean_completed_discovery(self):
        result = monthly_coverage([], [], CONFIG, [], '2026-10-25')
        self.assertEqual(len(result['months']), 10)
        self.assertEqual(result['months'][0]['publication_discovery_status'], 'not_started')
        self.assertEqual(result['months'][0]['window_month_status'], 'no_verified_events_yet')
        self.assertEqual(result['potential_pair_count'], 0)
        self.assertIsNone(result['actual_pair_count'])

    def test_unfinished_revenue_months_and_lag(self):
        rows = monthly_coverage([], [], CONFIG, [], '2026-10-25')['months']
        months = {row['window_end_month']:row for row in rows}
        self.assertEqual(months['2026-08']['revenue_month'], '2026-09')
        self.assertEqual(months['2026-08']['revenue_status'], 'missing_or_not_imported')
        self.assertEqual(months['2026-09']['revenue_status'], 'month_not_complete')
        self.assertEqual(months['2026-10']['revenue_month'], '2026-11')
        self.assertEqual(months['2026-10']['revenue_status'], 'month_not_complete')

    def test_end_september_rollover(self):
        result = monthly_coverage([event('2026-09-30T00:00:00Z')], [], CONFIG, [], '2026-10-25')
        self.assertEqual(result['months'][-1]['verified_event_count'], 1)
        self.assertEqual(result['months'][-1]['revenue_month'], '2026-11')

    def test_revised_candidate_boundaries(self):
        for timestamp, expected in [('2025-12-31T23:59:59Z',0), ('2026-01-01T00:00:00Z',1),
                                    ('2026-09-30T23:59:59Z',1), ('2026-10-01T00:00:00Z',0)]:
            self.assertEqual(audit([event(timestamp)], [], CONFIG)['included_verified_events'], expected)

    def test_completed_discovery_needs_evidence(self):
        with self.assertRaises(ValueError):
            monthly_coverage([], [], CONFIG, [dict(month='2026-01', discovery_status='completed', checked_at_utc='', evidence_notes='')], '2026-10-25')

    def test_mixed_text_package_retention_cap(self):
        permissions = dict(policy_review_status='documented', evidence_reference='SYNTHETIC',
                           policy_reviewed_at='2026-10-25', collection_allowed=True, retention_days=30)
        authorize({'dry_run':False}, permissions, 'collection_allowed')
        for retention in [31, 0, True]:
            with self.assertRaises(PermissionError):
                authorize({'dry_run':False}, {**permissions, 'retention_days':retention}, 'collection_allowed')
