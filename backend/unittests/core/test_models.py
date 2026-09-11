from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from application.core.models import Component, Observation, Product
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase


class TestParser(BaseTestCase):
    def test_str(self):
        parser = Parser(name="parser_name")
        self.assertEqual("parser_name", str(parser))


class TestObservation(BaseTestCase):
    def test_str(self):
        product = Product(name="product_name")
        observation = Observation(title="observation_title", product=product)
        self.assertEqual("product_name / observation_title", str(observation))

    def test_save(self):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )
        product = Product.objects.get(pk=1)

        observation = Observation(
            title="observation_title",
            product=product,
            import_last_seen=timezone.now(),
            parser=Parser.objects.first(),
            origin_component_name="component",
            origin_component_version="1.0.0",
        )
        observation.save()

        # check if pre_save signal is working
        self.assertEqual("4d0ea3fe1e7e00756da57c54073dd41e2e140ecf6b139d0780c3dedecd08db75", observation.identity_hash)
        self.assertEqual("component:1.0.0", observation.origin_component_name_version)
        product.refresh_from_db()
        self.assertTrue(1, product.has_component)


class TestObservationManager(BaseTestCase):
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
        Observation.objects.create(
            title="observation_manager_test",
            product=Product.objects.get(pk=1),
            import_last_seen=timezone.now(),
            parser=Parser.objects.first(),
            origin_component=self.component,
            origin_component_name="component",
            origin_component_version="1.0.0",
        )
