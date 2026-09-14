from importlib import import_module
from unittest.mock import patch

from django.apps import apps
from django.test import TestCase

from application.core.models import Component, Product
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result

migration = import_module("application.licenses.migrations.0024_initialize_license_component_components")


class TestInitializeLicenseComponentComponents(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="product")

    def _create_license_component(self, name_version: str) -> License_Component:
        return License_Component.objects.create(
            product=self.product,
            component_name=name_version.split(":")[0],
            component_version=name_version.split(":")[1],
            component_name_version=name_version,
            numerical_evaluation_result=License_Policy_Evaluation_Result.NUMERICAL_RESULTS[
                License_Policy_Evaluation_Result.RESULT_UNKNOWN
            ],
        )

    def test_initialize_license_component_components(self):
        license_component_1 = self._create_license_component("migration_component_1:1.0.0")
        license_component_2 = self._create_license_component("migration_component_1:1.0.0")
        license_component_3 = self._create_license_component("migration_component_2:2.0.0")

        # More license components than the batch size, so that the batching is used
        with patch.object(migration, "BATCH_SIZE", 2):
            migration.initialize_license_component_components(apps, None)

        license_component_1.refresh_from_db()
        license_component_2.refresh_from_db()
        license_component_3.refresh_from_db()

        self.assertEqual(2, Component.objects.filter(name_version__startswith="migration_component").count())
        self.assertEqual(license_component_1.component, license_component_2.component)
        self.assertNotEqual(license_component_1.component, license_component_3.component)
        self.assertEqual("migration_component_1:1.0.0", license_component_1.component.name_version)

    def test_initialize_license_component_components_is_repeatable(self):
        license_component = self._create_license_component("migration_component_1:1.0.0")

        migration.initialize_license_component_components(apps, None)
        license_component.refresh_from_db()
        component = license_component.component

        migration.initialize_license_component_components(apps, None)
        license_component.refresh_from_db()

        self.assertEqual(component, license_component.component)
        self.assertEqual(1, Component.objects.filter(name_version__startswith="migration_component").count())

    def test_migration_is_not_atomic(self):
        # One transaction per batch is what keeps the migration from deadlocking with a running installation
        self.assertFalse(migration.Migration.atomic)
