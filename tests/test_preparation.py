"""SYNTHETIC data only; local preparation and manual CSV validation."""
import os
import tempfile
import unittest
from pathlib import Path
from genshin_research.preparation import prepare_audit, revenue_report, TEMPLATES


def synthetic_revenue(**changes):
    return {**dict(month='2026-01', revenue_usd='100', platform_scope='SYNTHETIC mobile',
                   region_scope='TEST', cn_android_included='false', cn_android_multiplier='',
                   source_url='https://example.invalid/SYNTHETIC', retrieved_at='2026-02-02',
                   revision_notes='SYNTHETIC TEST VALUE; NOT RESEARCH DATA'), **changes}


class PreparationTests(unittest.TestCase):
    def test_initialization_preserves_work_and_rejects_external_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            old = os.getcwd()
            try:
                os.chdir(folder)
                Path('templates').mkdir()
                for name in TEMPLATES:
                    (Path('templates') / name).write_text('SYNTHETIC TEMPLATE\n')
                self.assertEqual(len(prepare_audit()['created']), 3)
                Path('data/events.csv').write_text('SYNTHETIC EDIT\n')
                self.assertEqual(len(prepare_audit()['preserved']), 3)
                self.assertEqual(Path('data/events.csv').read_text(), 'SYNTHETIC EDIT\n')
                with self.assertRaises(ValueError):
                    prepare_audit('outside_data')
            finally:
                os.chdir(old)

    def test_empty_import_is_not_source_verification(self):
        report = revenue_report([])
        self.assertEqual(report['status'], 'empty')
        self.assertFalse(report['source_verified'])

    def test_zero_is_observed_but_blank_is_missing(self):
        report = revenue_report([synthetic_revenue(revenue_usd='0')])
        self.assertEqual(report['available_months'], ['2026-01'])
        report = revenue_report([synthetic_revenue(revenue_usd='')])
        self.assertEqual(report['missing_value_months'], ['2026-01'])

    def test_reject_invalid_multiplier_flag_or_timestamp(self):
        for change in [dict(cn_android_multiplier='2'), dict(cn_android_included='yes'),
                       dict(retrieved_at='2026-02-02T00:00:00'), dict(cn_android_included='true',cn_android_multiplier='nan'),
                       dict(source_url='https://username:password@example.invalid/')]:
            with self.assertRaises(ValueError):
                revenue_report([synthetic_revenue(**change)])

    def test_unknown_scope_is_reported_not_treated_as_verified(self):
        report = revenue_report([synthetic_revenue(cn_android_included='unknown')])
        self.assertEqual(report['unknown_cn_android_months'], ['2026-01'])
        self.assertFalse(report['source_verified'])
