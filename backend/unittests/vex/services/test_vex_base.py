from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Branch,
    Observation,
    Observation_Log,
    Product,
    Product_Member,
)
from application.core.queries.observation import get_current_modifying_observation_log
from application.import_observations.models import Parser
from application.vex.models import VEX_Counter
from application.vex.services.vex_base import (
    create_document_base_id,
    get_observations_for_product,
    get_observations_for_vulnerabilities,
    get_observations_for_vulnerability,
)


class TestCreateDocumentBaseId(TestCase):
    def test_increments_per_prefix_and_year(self):
        year = timezone.now().year

        self.assertEqual(create_document_base_id("PREFIX"), f"{year}_0001")
        self.assertEqual(create_document_base_id("PREFIX"), f"{year}_0002")
        self.assertEqual(create_document_base_id("OTHER"), f"{year}_0001")

        self.assertEqual(VEX_Counter.objects.get(document_id_prefix="PREFIX", year=year).counter, 2)
        self.assertEqual(VEX_Counter.objects.get(document_id_prefix="OTHER", year=year).counter, 1)

    def test_locks_the_counter_row(self):
        # SQLite ignores select_for_update(), so the lock that keeps concurrent
        # requests from reading the same counter cannot be exercised here;
        # assert the lock is requested instead.
        counter = VEX_Counter(document_id_prefix="PREFIX", year=2026, counter=41)
        with patch("application.vex.services.vex_base.VEX_Counter.objects") as objects:
            objects.select_for_update.return_value.get_or_create.return_value = (counter, False)

            self.assertEqual(create_document_base_id("PREFIX"), "2026_0042")

            objects.select_for_update.assert_called_once_with()
            objects.select_for_update.return_value.get_or_create.assert_called_once_with(
                document_id_prefix="PREFIX", year=timezone.now().year
            )


class TestVexObservationPrefetch(TestCase):
    @patch("application.core.signals.get_current_user", return_value=None)
    def test_all_export_queries_prefetch_latest_modifying_logs_within_user_scope(self, _mock_signal_user):
        user = User.objects.create(username="vex-reader")
        parser = Parser.objects.create(name="vex-prefetch-test")
        product = Product.objects.create(name="visible")
        branch = Branch.objects.create(product=product, name="main")
        Product_Member.objects.create(product=product, user=user, role=Roles.Reader)
        observations = [
            Observation.objects.create(
                product=product,
                branch=branch,
                parser=parser,
                title=f"observation-{i}",
                vulnerability_id="CVE-2026-1234",
                import_last_seen=timezone.now(),
            )
            for i in range(3)
        ]
        expected = {}
        for observation in observations[:2]:
            Observation_Log.objects.create(observation=observation, user=user, status="Open", comment="old")
            latest = Observation_Log.objects.create(
                observation=observation, user=user, vex_justification="component_not_present", comment="latest"
            )
            Observation_Log.objects.create(observation=observation, user=user, comment="newer non-modifying log")
            expected[observation.pk] = latest.pk
        expected[observations[2].pk] = None
        hidden = Product.objects.create(name="hidden")
        Observation.objects.create(
            product=hidden,
            parser=parser,
            title="hidden",
            vulnerability_id="CVE-2026-1234",
            import_last_seen=timezone.now(),
        )

        for observation in observations:
            log = get_current_modifying_observation_log(observation)
            self.assertEqual(log.pk if log else None, expected[observation.pk])

        getters = (
            lambda: get_observations_for_product(product, ["CVE-2026-1234"], [branch]),
            lambda: get_observations_for_vulnerability("CVE-2026-1234"),
            lambda: get_observations_for_vulnerabilities(["CVE-2026-1234"]),
        )
        with patch("application.core.queries.observation.get_current_user", return_value=user):
            for index, getter in enumerate(getters):
                with self.subTest(export_query=index), self.assertNumQueries(4):
                    loaded = getter()
                    self.assertEqual([item.pk for item in loaded], [item.pk for item in observations])
                    for observation in loaded:
                        self.assertEqual(observation.product.name, "visible")
                        self.assertEqual(observation.branch.name, "main")
                        log = get_current_modifying_observation_log(observation)
                        self.assertEqual(log.pk if log else None, expected[observation.pk])
