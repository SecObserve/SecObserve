from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

from application.core.models import Component, Product
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase


class TestLicenseComponentManager(BaseTestCase):
    def setUp(self):
        super().setUp()
        call_command(
            "loaddata",
            [
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )
        self.component = Component.objects.create(
            identity_hash="identity_hash",
            name="component",
            version="1.0.0",
            name_version="component:1.0.0",
        )
        License_Component.objects.create(
            product=Product.objects.get(pk=1),
            identity_hash="license_component_identity_hash",
            numerical_evaluation_result=5,
            component=self.component,
            component_name="component",
            component_version="1.0.0",
            component_name_version="component:1.0.0",
        )

    def test_component_does_not_need_an_extra_query(self):
        with CaptureQueriesContext(connection) as captured_queries:
            license_components = list(License_Component.objects.filter(component_name="component"))
            for license_component in license_components:
                self.assertEqual(self.component, license_component.component)

        self.assertEqual(1, len(captured_queries.captured_queries))
        self.assertIn("JOIN", captured_queries.captured_queries[0]["sql"].upper())

    def test_count_does_not_join_the_component(self):
        with CaptureQueriesContext(connection) as captured_queries:
            self.assertEqual(1, License_Component.objects.filter(component_name="component").count())

        self.assertNotIn("JOIN", captured_queries.captured_queries[0]["sql"].upper())
