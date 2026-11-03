import unittest

from application.commons.services.security_gate_conditions import (
    conditions_have_a_rule,
    normalize_security_gate_conditions,
)

KEV = {"known_exploited": True}


class TestNormalizeSecurityGateConditions(unittest.TestCase):
    def test_fills_defaults(self):
        result = normalize_security_gate_conditions({"default": [KEV]})

        self.assertEqual(
            result,
            {
                "default": [
                    {
                        "operator": "any",
                        "known_exploited": True,
                        "exploit_tooling": False,
                        "proof_of_concept": False,
                        "epss_min": None,
                        "network_vector": False,
                        "fix_available": False,
                    }
                ],
                "severities": {},
            },
        )

    def test_keeps_decimal_epss(self):
        result = normalize_security_gate_conditions({"default": [{"epss_min": 0.5}]})

        self.assertEqual(result["default"][0]["epss_min"], 0.5)

    def test_empty_override_is_kept(self):
        result = normalize_security_gate_conditions({"severities": {"Medium": []}})

        self.assertEqual(result["severities"], {"Medium": []})

    def test_rejects_unknown_severity(self):
        with self.assertRaisesRegex(ValueError, "Unknown severity 'Severe'"):
            normalize_security_gate_conditions({"severities": {"Severe": [KEV]}})

    def test_rejects_unknown_condition(self):
        with self.assertRaisesRegex(ValueError, "Unknown condition 'reachable'"):
            normalize_security_gate_conditions({"default": [{"reachable": True}]})

    def test_rejects_unknown_key(self):
        with self.assertRaisesRegex(ValueError, "Unknown key 'rules'"):
            normalize_security_gate_conditions({"rules": []})

    def test_rejects_bad_operator(self):
        with self.assertRaisesRegex(ValueError, "Operator"):
            normalize_security_gate_conditions({"default": [{"operator": "nor", **KEV}]})

    def test_rejects_epss_out_of_range(self):
        with self.assertRaisesRegex(ValueError, "EPSS"):
            normalize_security_gate_conditions({"default": [{"epss_min": 101}]})

    def test_rejects_rules_not_a_list(self):
        with self.assertRaisesRegex(ValueError, "Rules must be a list"):
            normalize_security_gate_conditions({"default": KEV})

    def test_rule_requires_a_condition(self):
        with self.assertRaisesRegex(ValueError, "at least one enabled condition"):
            normalize_security_gate_conditions({"default": [{"operator": "all"}]})

    def test_not_an_object(self):
        with self.assertRaisesRegex(ValueError, "object with 'default'"):
            normalize_security_gate_conditions(["Critical"])

    def test_empty_is_valid(self):
        self.assertEqual(normalize_security_gate_conditions({}), {"default": [], "severities": {}})

    def test_none_is_valid(self):
        self.assertEqual(normalize_security_gate_conditions(None), {"default": [], "severities": {}})


class TestConditionsHaveARule(unittest.TestCase):
    def test_no_rule(self):
        self.assertFalse(conditions_have_a_rule({"default": [], "severities": {"Medium": []}}))

    def test_rule_in_severity(self):
        self.assertTrue(conditions_have_a_rule({"default": [], "severities": {"High": [KEV]}}))

    def test_rule_in_default(self):
        self.assertTrue(conditions_have_a_rule({"default": [KEV], "severities": {}}))
