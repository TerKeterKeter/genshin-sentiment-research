"""SYNTHETIC registry fixtures; no real video or API data."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from genshin_research.audit import audit
from genshin_research.cli import main
from genshin_research.core import write_json
from genshin_research.management import purge_package
from genshin_research.preparation import prepare_audit

CONFIG = {'candidate_start':'2026-01-01','candidate_end_exclusive':'2026-10-01','dry_run':True}


def event(**changes):
    return {**dict(event_id='SYNTHETIC', character_name='TEST', video_id='TEST',
        video_url='https://example.invalid/TEST', announcement_source_url='https://example.invalid/ANNOUNCEMENT',
        initial_announcement_at_utc='2026-03-01T00:00:00Z', channel_id='TEST_OFFICIAL',
        video_published_at_utc='2026-03-01T00:01:00Z', content_type='verified_initial_drip_short',
        inclusion_status='included', exclusion_reason='', verification_notes='SYNTHETIC HUMAN DECISION'), **changes}


class RegistryTests(unittest.TestCase):
    def test_pending_is_not_accepted(self):
        result = audit([event(inclusion_status='pending')], CONFIG, [])
        self.assertEqual(result['included_verified_events'], 0)
        self.assertEqual(result['pending_events'], ['SYNTHETIC'])
        self.assertEqual(result['discovery_by_month']['2026-01'], 'not_started')

    def test_included_requires_manual_evidence(self):
        result = audit([event(verification_notes='')], CONFIG, [])
        self.assertTrue(result['issues'])
        self.assertEqual(result['included_verified_events'], 0)
        self.assertEqual(audit([event()], CONFIG, [])['events_by_publication_month'], {'2026-03':1})

    def test_period_boundaries(self):
        for timestamp, expected in [('2025-12-31T23:59:59Z',0),('2026-01-01T00:00:00Z',1),
            ('2026-09-30T23:59:59Z',1),('2026-10-01T00:00:00Z',0)]:
            self.assertEqual(audit([event(video_published_at_utc=timestamp)], CONFIG, [])['included_verified_events'], expected)

    def test_duplicate_and_typo_are_reported(self):
        self.assertTrue(audit([event(), event()], CONFIG, [])['issues'])
        self.assertTrue(audit([event(), event(event_id='SECOND')], CONFIG, [])['issues'])
        self.assertTrue(audit([event(inclusion_status='inclued')], CONFIG, [])['issues'])

    def test_exclusion_and_discovery_need_reasons(self):
        self.assertTrue(audit([event(inclusion_status='excluded')], CONFIG, [])['issues'])
        row = dict(month='2026-01', discovery_status='completed', checked_at_utc='', evidence_notes='')
        self.assertTrue(audit([], CONFIG, [row])['issues'])
        row.update(checked_at_utc='2026-10-25T00:00:00Z', evidence_notes='SYNTHETIC SEARCH LOG')
        self.assertFalse(audit([], CONFIG, [row])['issues'])


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temporary.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temporary.cleanup()

    def test_prepare_preserves_existing_files(self):
        Path('templates').mkdir()
        for name in ['events.csv','discovery_coverage.csv']:
            (Path('templates')/name).write_text('SYNTHETIC TEMPLATE\n')
        self.assertEqual(len(prepare_audit()['created']), 2)
        Path('data/events.csv').write_text('SYNTHETIC EDIT\n')
        self.assertEqual(len(prepare_audit()['preserved']), 2)
        self.assertEqual(Path('data/events.csv').read_text(), 'SYNTHETIC EDIT\n')
        with self.assertRaises(ValueError): prepare_audit('outside')

    def test_metadata_cli_preserves_scope_and_records_evidence(self):
        write_json('config.json', {**CONFIG,'dry_run':False})
        write_json('permissions.json', dict(policy_review_status='documented',policy_reviewed_at='2026-10-25',
            evidence_reference='SYNTHETIC',metadata_allowed=True,retention_days=30))
        api = Mock()
        api.metadata.return_value = {'video_id':'-TEST','channel_id':'TEST_OFFICIAL'}
        api.official_channel_id.return_value = 'TEST_OFFICIAL'
        output = io.StringIO()
        with patch('genshin_research.cli.YouTube',return_value=api), redirect_stdout(output):
            main(['metadata','--package','data/test','--','-TEST'])
        result = json.loads(output.getvalue())
        self.assertTrue(result['matches_official_channel'])
        self.assertNotIn('inclusion_status', result)
        self.assertTrue(Path('data/test/manifest.json').exists())
        api.assert_not_called()

    def test_dry_run_never_creates_api_client(self):
        write_json('config.json', CONFIG)
        write_json('permissions.json', {})
        with patch('genshin_research.cli.YouTube') as api:
            with self.assertRaises(PermissionError): main(['metadata','TEST'])
        api.assert_not_called()

    def test_purge_expiry_and_path(self):
        Path('data/test').mkdir(parents=True)
        write_json('data/test/manifest.json', {'expires_at':'2026-01-02T00:00:00Z'})
        self.assertFalse(purge_package('data/test',now=datetime(2026,1,1,tzinfo=timezone.utc)))
        self.assertTrue(purge_package('data/test',now=datetime(2026,1,3,tzinfo=timezone.utc)))
        with self.assertRaises(ValueError): purge_package('.',force=True)


class TransportTests(unittest.TestCase):
    def test_transient_error_retried(self):
        from genshin_research.youtube import YouTube
        responses = [Mock(status_code=429),Mock(status_code=200)]
        responses[1].json.return_value = {'items':[]}
        with patch('requests.get',side_effect=responses) as request, patch('time.sleep'):
            self.assertEqual(YouTube('SYNTHETIC_KEY')('videos',{}), {'items':[]})
            self.assertEqual(request.call_count,2)

    def test_permission_error_not_retried(self):
        from genshin_research.youtube import YouTube
        with patch('requests.get',return_value=Mock(status_code=403)) as request:
            with self.assertRaisesRegex(RuntimeError,'HTTP 403'): YouTube('SYNTHETIC_KEY')('videos',{})
            self.assertEqual(request.call_count,1)
