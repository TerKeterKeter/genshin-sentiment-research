"""SYNTHETIC CLI regression tests; API transport is mocked throughout."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from genshin_research.cli import main
from genshin_research.core import read_csv, write_csv, write_json


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temporary.name)
        self.config = {
            'dry_run': False, 'candidate_start': '2026-01-01',
            'candidate_end_exclusive': '2026-10-01', 'window_hours': 72,
            'language': 'en', 'random_seed': 42,
        }
        self.permissions = {
            'policy_review_status': 'documented', 'policy_reviewed_at': '2026-10-25',
            'evidence_reference': 'SYNTHETIC TEST PERMISSION', 'retention_days': 30,
            'metadata_allowed': True, 'collection_allowed': True,
            'derived_analysis_allowed': True, 'external_join_allowed': False,
        }
        write_json('config.json', self.config)
        write_json('permissions.json', self.permissions)

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.temporary.cleanup()

    def invoke(self, args):
        output = io.StringIO()
        with redirect_stdout(output):
            main(args)
        return output.getvalue()

    def test_metadata_cli_saves_evidence_without_classifying_event(self):
        api = Mock()
        api.metadata.return_value = {'video_id': '-TEST', 'channel_id': 'TEST_OFFICIAL'}
        api.official_channel_id.return_value = 'TEST_OFFICIAL'
        with patch('genshin_research.commands.YouTube', return_value=api):
            report = json.loads(self.invoke(['metadata', '--package', 'data/test', '--', '-TEST']))
        self.assertTrue(report['matches_official_channel'])
        self.assertNotIn('inclusion_status', report)
        self.assertTrue(Path('data/test/manifest.json').exists())
        self.assertTrue(Path('data/test/metadata.json').exists())
        api.assert_not_called()  # No comment endpoint.

    def test_dry_run_rejects_network_before_client_is_created(self):
        write_json('config.json', {**self.config, 'dry_run': True})
        with patch('genshin_research.commands.YouTube') as api:
            with self.assertRaises(PermissionError):
                self.invoke(['metadata', 'TEST'])
        api.assert_not_called()

    def test_collection_cli_preserves_manifest_comments_and_completion(self):
        timestamp = '2026-03-01T00:00:00Z'
        event = dict(event_id='SYNTHETIC', character_name='TEST', announcement_source_url='https://example.invalid/TEST',
            initial_announcement_at_utc=timestamp, video_id='TEST', video_url='https://example.invalid/TEST',
            channel_id='TEST_OFFICIAL', video_published_at_utc=timestamp, content_type='verified_initial_drip_short',
            inclusion_status='included', verification_notes='SYNTHETIC REVIEW')
        write_csv('events.csv', [event])
        api = Mock()
        api.official_channel_id.return_value = 'TEST_OFFICIAL'
        api.metadata.return_value = {'channel_id':'TEST_OFFICIAL', 'video_published_at_utc':timestamp}
        api.return_value = {'items': [{'snippet': {'topLevelComment': {'id':'SYNTHETIC_COMMENT', 'snippet': {
            'textDisplay':'SYNTHETIC TEST TEXT', 'publishedAt':timestamp, 'updatedAt':timestamp, 'likeCount':0,
        }}}}]}
        with patch('genshin_research.commands.YouTube', return_value=api):
            report = json.loads(self.invoke(['collect','--events','events.csv','--package','data/test']))
        self.assertTrue(report[0]['pagination_complete'])
        self.assertEqual(read_csv('data/test/comments.csv')[0]['comment_id'], 'SYNTHETIC_COMMENT')
        self.assertTrue(Path('data/test/collection_status.json').exists())
        self.assertTrue(Path('data/test/manifest.json').exists())

    def test_incomplete_collection_cannot_reach_model(self):
        Path('data/test').mkdir(parents=True)
        write_json('data/test/manifest.json', {'expires_at':'2099-01-01T00:00:00Z'})
        write_json('data/test/collection_status.json', [{'pagination_complete':False}])
        with patch('genshin_research.commands.infer') as model:
            with self.assertRaisesRegex(ValueError, 'Incomplete collection'):
                self.invoke(['nlp','--package','data/test'])
        model.assert_not_called()

    def test_expired_collection_cannot_reach_model(self):
        Path('data/test').mkdir(parents=True)
        write_json('data/test/manifest.json', {'expires_at':'2000-01-01T00:00:00Z'})
        with patch('genshin_research.commands.infer') as model:
            with self.assertRaisesRegex(ValueError, 'Package expired'):
                self.invoke(['nlp','--package','data/test'])
        model.assert_not_called()
