from importlib import import_module
from unittest.mock import patch

from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from application.core.models import Component, Observation, Product
from application.core.types import Status
from application.import_observations.models import Parser
from application.import_observations.types import Parser_Source, Parser_Type

migration = import_module("application.core.migrations.0099_initialize_observation_components")


class TestInitializeObservationComponents(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="product")
        self.parser = Parser.objects.create(name="parser", type=Parser_Type.TYPE_SCA, source=Parser_Source.SOURCE_FILE)

    def _create_observation(self, name_version: str) -> Observation:
        return Observation.objects.create(
            title=f"observation_{name_version}",
            product=self.product,
            parser=self.parser,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
            origin_component_name=name_version.split(":")[0],
            origin_component_version=name_version.split(":")[1],
            origin_component_name_version=name_version,
        )

    def test_initialize_observation_components(self):
        observation_1 = self._create_observation("migration_component_1:1.0.0")
        observation_2 = self._create_observation("migration_component_1:1.0.0")
        observation_3 = self._create_observation("migration_component_2:2.0.0")
        observation_without_component = Observation.objects.create(
            title="observation_without_component",
            product=self.product,
            parser=self.parser,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

        # More observations than the batch size, so that the batching is used
        with patch.object(migration, "BATCH_SIZE", 2):
            migration.initialize_observation_components(apps, None)

        observation_1.refresh_from_db()
        observation_2.refresh_from_db()
        observation_3.refresh_from_db()
        observation_without_component.refresh_from_db()

        self.assertEqual(2, Component.objects.filter(name_version__startswith="migration_component").count())
        self.assertEqual(observation_1.origin_component, observation_2.origin_component)
        self.assertNotEqual(observation_1.origin_component, observation_3.origin_component)
        self.assertEqual("migration_component_1:1.0.0", observation_1.origin_component.name_version)
        self.assertIsNone(observation_without_component.origin_component)

    def test_initialize_observation_components_is_repeatable(self):
        observation = self._create_observation("migration_component_1:1.0.0")

        migration.initialize_observation_components(apps, None)
        observation.refresh_from_db()
        component = observation.origin_component

        migration.initialize_observation_components(apps, None)
        observation.refresh_from_db()

        self.assertEqual(component, observation.origin_component)
        self.assertEqual(1, Component.objects.filter(name_version__startswith="migration_component").count())

    def test_migration_is_not_atomic(self):
        # One transaction per batch is what keeps the migration from deadlocking with a running installation
        self.assertFalse(migration.Migration.atomic)
