from application.vex.services.csaf_parser import (
    _get_impact,
    _get_justification,
    _get_remediation,
    _process_product_groups,
    _resolve_product_ids,
)
from unittests.base_test_case import BaseTestCase


class TestCSAFParser(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.groups = {"GROUP-1": ["PRODUCT-1", "PRODUCT-2"]}

    def test_process_product_groups(self):
        product_tree = {
            "product_groups": [
                {"group_id": "GROUP-1", "product_ids": ["PRODUCT-1", "PRODUCT-2"]},
                {"product_ids": ["PRODUCT-3"]},
                {"group_id": "GROUP-2"},
            ]
        }

        self.assertEqual({"GROUP-1": ["PRODUCT-1", "PRODUCT-2"], "GROUP-2": []}, _process_product_groups(product_tree))

    def test_process_product_groups_empty(self):
        self.assertEqual({}, _process_product_groups({}))

    def test_resolve_product_ids(self):
        item = {"product_ids": ["PRODUCT-3"], "group_ids": ["GROUP-1", "GROUP-UNKNOWN"]}

        self.assertEqual({"PRODUCT-1", "PRODUCT-2", "PRODUCT-3"}, _resolve_product_ids(item, self.groups))

    def test_get_remediation_group(self):
        vulnerability = {
            "remediations": [
                {"category": "vendor_fix", "group_ids": ["GROUP-1"], "details": "Vendor fix"},
                {"category": "mitigation", "group_ids": ["GROUP-1"], "details": "Mitigation"},
            ]
        }

        self.assertEqual("Mitigation", _get_remediation(vulnerability, "PRODUCT-2", self.groups))
        self.assertEqual("", _get_remediation(vulnerability, "PRODUCT-3", self.groups))

    def test_get_justification_group(self):
        vulnerability = {"flags": [{"label": "component_not_present", "group_ids": ["GROUP-1"]}]}

        self.assertEqual("component_not_present", _get_justification(vulnerability, "PRODUCT-1", self.groups))
        self.assertEqual("", _get_justification(vulnerability, "PRODUCT-3", self.groups))

    def test_get_impact_group(self):
        vulnerability = {
            "threats": [
                {"category": "exploit_status", "group_ids": ["GROUP-1"], "details": "Exploit status"},
                {"category": "impact", "group_ids": ["GROUP-1"], "details": "Impact"},
            ]
        }

        self.assertEqual("Impact", _get_impact(vulnerability, "PRODUCT-1", self.groups))
        self.assertEqual("", _get_impact(vulnerability, "PRODUCT-3", self.groups))

    def test_get_impact_product(self):
        vulnerability = {"threats": [{"category": "impact", "product_ids": ["PRODUCT-3"], "details": "Impact"}]}

        self.assertEqual("Impact", _get_impact(vulnerability, "PRODUCT-3", self.groups))
