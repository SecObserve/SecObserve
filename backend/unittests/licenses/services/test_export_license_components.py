from datetime import datetime

from django.core.management import call_command

from application.core.models import Product
from application.licenses.services.export_license_components import export_license_components_excel
from unittests.base_test_case import BaseTestCase


class TestLicenseGroupMemberSerializer(BaseTestCase):
    @classmethod
    def setUpClass(self):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )

        super().setUpClass()

    def test_export_license_components_excel(self):
        product = Product.objects.get(pk=1)

        workbook = export_license_components_excel(product)
        worksheet = workbook["License Components"]

        i = 0
        for row in worksheet.rows:
            i += 1
            self.assertEqual(45, len(row))
        self.assertEqual(2, i)

        actual_values = []
        for row in worksheet.values:
            for value in row:
                actual_values.append(value)
        expected_values = [
            "Branch",
            "Branch id",
            "Component cpe",
            "Component cyclonedx bom link",
            "Component dependencies",
            "Component name",
            "Component name version",
            "Component purl",
            "Component purl type",
            "Component version",
            "Created",
            "Effective license expression",
            "Effective license name",
            "Effective multiple licenses",
            "Effective non spdx license",
            "Effective spdx license",
            "Effective spdx license id",
            "Evaluation result",
            "Id",
            "Import last seen",
            "Imported concluded license expression",
            "Imported concluded license name",
            "Imported concluded multiple licenses",
            "Imported concluded non spdx license",
            "Imported concluded spdx license",
            "Imported concluded spdx license id",
            "Imported declared license expression",
            "Imported declared license name",
            "Imported declared multiple licenses",
            "Imported declared non spdx license",
            "Imported declared spdx license",
            "Imported declared spdx license id",
            "Last change",
            "Manual concluded comment",
            "Manual concluded license expression",
            "Manual concluded license name",
            "Manual concluded non spdx license",
            "Manual concluded spdx license",
            "Manual concluded spdx license id",
            "Numerical evaluation result",
            "Origin service",
            "Origin service id",
            "Product",
            "Product id",
            "Upload filename",
            None,
            None,
            "",
            "",
            "",
            "internal_component",
            "internal_component:1.0.0",
            "",
            "",
            "1.0.0",
            datetime(2022, 12, 15, 16, 10, 35, 513000),
            "",
            "No license information",
            "",
            "",
            None,
            None,
            "Allowed",
            1,
            datetime(2022, 12, 15, 16, 10, 35, 513000),
            "",
            "No license information",
            "",
            "",
            None,
            None,
            "",
            "internal license",
            "",
            "internal license",
            None,
            None,
            datetime(2022, 12, 15, 16, 10, 35, 513000),
            "",
            "",
            "No license information",
            "",
            None,
            None,
            1,
            None,
            None,
            "db_product_internal",
            1,
            "",
        ]
        self.assertEqual(expected_values, actual_values)
