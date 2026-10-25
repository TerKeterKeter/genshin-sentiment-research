"""SYNTHETIC metadata only; no network or real credentials."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from genshin_research.metadata_audit import verify_metadata, save_metadata_package
from genshin_research.core import authorize


class MetadataAuditTests(unittest.TestCase):
    def test_official_channel_match_and_mismatch(self):
        for channel, match in [('TEST_OFFICIAL', True), ('TEST_OTHER', False)]:
            api = Mock()
            api.metadata.return_value = {'video_id':'TEST', 'channel_id':channel}
            api.official_channel_id.return_value = 'TEST_OFFICIAL'
            self.assertEqual(verify_metadata(api, 'TEST')['matches_official_channel'], match)
            api.metadata.assert_called_once_with('TEST')
            api.official_channel_id.assert_called_once_with()
            api.assert_not_called()  # No comment endpoint calls.

    def test_metadata_permission_does_not_enable_comments_or_inference(self):
        permissions = dict(policy_review_status='documented', evidence_reference='SYNTHETIC_SCOPE',
            policy_reviewed_at='2026-10-25', metadata_allowed=True, retention_days=30,
            collection_allowed=False, derived_analysis_allowed=False, external_join_allowed=False)
        authorize({'dry_run':False}, permissions, 'metadata_allowed')
        for operation in ['collection_allowed','derived_analysis_allowed','external_join_allowed']:
            with self.assertRaises(PermissionError):
                authorize({'dry_run':False}, permissions, operation)
        with self.assertRaises(PermissionError):
            authorize({'dry_run':True}, permissions, 'metadata_allowed')

    def test_package_expiry_path_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            old = os.getcwd()
            try:
                os.chdir(folder)
                path = Path(save_metadata_package({'video_id':'SYNTHETIC'}, 'data/test', 30))
                manifest = json.loads((path/'manifest.json').read_text())
                self.assertEqual(manifest['kind'], 'metadata_only')
                self.assertIn('expires_at', manifest)
                with self.assertRaises(FileExistsError):
                    save_metadata_package({}, 'data/test', 30)
                with self.assertRaises(ValueError):
                    save_metadata_package({}, 'outside', 30)
                with self.assertRaises(ValueError):
                    save_metadata_package({}, 'data/invalid', 31)
            finally:
                os.chdir(old)
