"""SYNTHETIC IDs and local CSV only; no network calls."""
import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from genshin_research.cli import main
from genshin_research.core import read_csv
from genshin_research.registry import EVENT_FIELDS, register_candidate, video_id_from_input

VIDEO = 'AbCdEfGhI12'


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temporary.name)
        Path('data').mkdir()
        with Path('data/events.csv').open('w', newline='', encoding='utf-8') as stream:
            csv.DictWriter(stream, fieldnames=EVENT_FIELDS).writeheader()

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temporary.cleanup()

    def test_cli_registers_offline_pending_without_dates_or_classification(self):
        output = io.StringIO()
        with patch('genshin_research.cli.YouTube') as api, redirect_stdout(output):
            main(['register', f'https://www.youtube.com/shorts/{VIDEO}?si=tracking', '--character', 'SYNTHETIC'])
        api.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())['event_id'], 'candidate_001')
        row = read_csv('data/events.csv')[0]
        self.assertEqual(row['inclusion_status'], 'pending')
        self.assertEqual(row['character_name'], 'SYNTHETIC')
        self.assertEqual(row['video_url'], f'https://youtube.com/shorts/{VIDEO}')
        for field in ['video_published_at_utc','initial_announcement_at_utc','channel_id','content_type']:
            self.assertEqual(row[field], '')

    def test_duplicate_preserves_file_bytes(self):
        register_candidate(VIDEO, character='SYNTHETIC ORIGINAL')
        before = Path('data/events.csv').read_bytes()
        result = register_candidate(VIDEO, character='DO NOT REPLACE')
        self.assertEqual(result['status'], 'already_registered')
        self.assertEqual(Path('data/events.csv').read_bytes(), before)

    def test_append_preserves_old_bytes_and_allocates_ids(self):
        register_candidate(VIDEO)
        before = Path('data/events.csv').read_bytes()
        result = register_candidate('-ABCDEFGHIJ')
        self.assertEqual(result['event_id'], 'candidate_002')
        self.assertTrue(Path('data/events.csv').read_bytes().startswith(before))
        self.assertEqual(len(read_csv('data/events.csv')), 2)

    def test_invalid_links_cannot_modify_registry(self):
        before = Path('data/events.csv').read_bytes()
        for value in ['https://example.com/shorts/'+VIDEO, 'https://youtube.com/watch?v='+VIDEO,
                      'https://youtube.com.evil.invalid/shorts/'+VIDEO, 'https://user:pass@youtube.com/shorts/'+VIDEO,
                      'https://youtube.com/shorts/invalid', 'not a link']:
            with self.assertRaises(ValueError): register_candidate(value)
        self.assertEqual(Path('data/events.csv').read_bytes(), before)

    def test_custom_registry_path_must_be_local_data(self):
        with self.assertRaises(ValueError): register_candidate(VIDEO, events='templates/events.csv')
        with self.assertRaises(FileNotFoundError): register_candidate(VIDEO, events='data/missing.csv')

    def test_negative_id_and_trailing_slash(self):
        self.assertEqual(video_id_from_input('-ABCDEFGHIJ'), '-ABCDEFGHIJ')
        self.assertEqual(video_id_from_input(f'https://m.youtube.com/shorts/{VIDEO}/'), VIDEO)

    def test_excel_utf8_bom_remains_readable_after_registration(self):
        path = Path('data/events.csv')
        path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8-sig')
        register_candidate(VIDEO, character='SYNTHETIC')
        before = path.read_bytes()
        register_candidate('-ABCDEFGHIJ')
        self.assertTrue(path.read_bytes().startswith(before))
        self.assertEqual(read_csv(path)[0]['event_id'], 'candidate_001')
        self.assertEqual(len(read_csv(path)), 2)
