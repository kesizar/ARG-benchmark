"""Outcome rates require explicit scope and complete, trustworthy observations."""
import unittest

from harness.test_protocol_v1 import ReportTests
from harness.protocol_report import report


class OutcomeReportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ReportTests()
        self.manifest = self.fixture.manifest()
        self.manifest['tasks'][0]['good_ending_scored'] = True
        self.manifest['tasks'][0]['terminal_failure_scored'] = True

    def rows(self):
        rows = [self.fixture.episode(self.manifest, i, i == 1) for i in range(1, 4)]
        rows[0].update(good_ending=True, ending_reached=True, ending_tier='good', failure_reached=False)
        rows[1].update(good_ending=False, ending_reached=True, ending_tier='normal', failure_reached=False)
        rows[2].update(good_ending=False, ending_reached=False, ending_tier=None, failure_reached=True, ended_reason='failure')
        return rows

    def outcome(self, rows):
        return next(x for x in report(self.manifest, rows)['models'] if x['model'] == 'm')

    def test_rates_have_explicit_scope_and_equal_task_weight(self):
        result = self.outcome(self.rows())
        self.assertEqual(result['good_ending_rate_macro'], 1 / 3)
        self.assertEqual(result['terminal_failure_rate_macro'], 1 / 3)
        self.assertEqual(result['good_ending_tasks'], 1)
        self.assertEqual(result['terminal_failure_completed_tasks'], 1)
        self.assertEqual(result['per_task'][0]['good_ending_observed_runs'], 3)

    def test_missing_or_unranked_is_not_zero(self):
        rows = self.rows()
        del rows[1]['failure_reached']
        rows[1]['ending_tier'] = None
        result = self.outcome(rows)
        self.assertIsNone(result['good_ending_rate_macro'])
        self.assertIsNone(result['terminal_failure_rate_macro'])
        self.assertEqual(result['per_task'][0]['good_ending_observed_runs'], 2)
        self.assertEqual(result['per_task'][0]['terminal_failure_observed_runs'], 2)

    def test_two_tasks_macro_and_incomplete_subset(self):
        second = dict(self.manifest['tasks'][0], id='other')
        self.manifest['tasks'].append(second)
        rows = self.rows()
        for i in range(1, 4):
            row = self.fixture.episode(self.manifest, i, True)
            row.update(task_id='other', good_ending=True, ending_reached=True,
                       ending_tier='good', failure_reached=False)
            row['protocol_identity']['run_id'] = 'other-' + str(i)
            rows.append(row)
        result = self.outcome(rows)
        self.assertAlmostEqual(result['good_ending_rate_macro'], (1 / 3 + 1) / 2)
        self.assertAlmostEqual(result['terminal_failure_rate_macro'], (1 / 3 + 0) / 2)
        self.assertIsNone(self.outcome(rows[:-1])['good_ending_rate_macro'])

    def test_unspecified_scope_does_not_report_rates(self):
        del self.manifest['tasks'][0]['good_ending_scored']
        del self.manifest['tasks'][0]['terminal_failure_scored']
        result = self.outcome(self.rows())
        self.assertEqual(result['good_ending_tasks'], 0)
        self.assertIsNone(result['good_ending_rate_macro'])
        self.assertIsNone(result['terminal_failure_rate_macro'])

    def test_non_boolean_scope_rejected(self):
        self.manifest['tasks'][0]['good_ending_scored'] = 'yes'
        with self.assertRaises(ValueError):
            report(self.manifest, [])


if __name__ == '__main__':
    unittest.main()
