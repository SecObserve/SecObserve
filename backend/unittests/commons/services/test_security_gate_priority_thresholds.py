from unittest import TestCase

from application.commons.services.security_gate_priority_thresholds import (
    normalize_security_gate_priority_thresholds,
)


class TestNormalizeSecurityGatePriorityThresholds(TestCase):
    def test_none_is_empty_list(self):
        self.assertEqual(normalize_security_gate_priority_thresholds(None), [])

    def test_sorted_by_priority(self):
        value = [{"priority": 3, "threshold": 5}, {"priority": 1, "threshold": 0}]
        self.assertEqual(
            normalize_security_gate_priority_thresholds(value),
            [{"priority": 1, "threshold": 0}, {"priority": 3, "threshold": 5}],
        )

    def test_rejects_duplicate_priority(self):
        with self.assertRaisesRegex(ValueError, "Priority 1 is listed twice"):
            normalize_security_gate_priority_thresholds(
                [{"priority": 1, "threshold": 0}, {"priority": 1, "threshold": 2}]
            )

    def test_rejects_priority_out_of_range(self):
        for priority in (0, 100):
            with self.assertRaisesRegex(ValueError, "Priority must be a number between 1 and 99"):
                normalize_security_gate_priority_thresholds([{"priority": priority, "threshold": 0}])

    def test_rejects_threshold_out_of_range_or_wrong_type(self):
        for threshold in (-1, 1000000, True, "0"):
            with self.assertRaisesRegex(ValueError, "Threshold must be a number between 0 and 999999"):
                normalize_security_gate_priority_thresholds([{"priority": 1, "threshold": threshold}])

    def test_rejects_unknown_key_and_non_list(self):
        with self.assertRaisesRegex(ValueError, "Unknown key 'severity'"):
            normalize_security_gate_priority_thresholds([{"priority": 1, "threshold": 0, "severity": "x"}])
        with self.assertRaisesRegex(ValueError, "Priority thresholds must be a list"):
            normalize_security_gate_priority_thresholds({"priority": 1})
