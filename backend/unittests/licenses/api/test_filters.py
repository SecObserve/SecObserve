from application.licenses.api.filters import LicenseComponentFilter
from unittests.base_test_case import BaseTestCase


class TestLicenseComponentFilter(BaseTestCase):
    def test_ordering_component_name_version(self):
        param_map = LicenseComponentFilter.base_filters["ordering"].param_map

        self.assertEqual(
            ("component_name", "component_version", "component_purl_type"),
            param_map["component_name_version"],
        )
        self.assertEqual("component_name_version", param_map["component_name_version_type"])
