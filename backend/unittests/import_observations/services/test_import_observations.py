import json
import os
import tempfile
from unittest.mock import call, patch

from django.core.files.base import File
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import (
    Branch,
    Evidence,
    Observation,
    Observation_Log,
    Product,
    Reference,
    Service,
)
from application.core.services.observation import (
    normalize_observation_fields,
)
from application.core.types import (
    Assessment_Status,
    Observation_Log_Comment,
    Severity,
    Status,
)
from application.epss.models import Exploit_Information
from application.import_observations.models import (
    Api_Configuration,
    Parser,
    Vulnerability_Check,
)
from application.import_observations.parsers.dependency_track.parser import (
    DependencyTrack,
)
from application.import_observations.services.import_license_components import (
    process_license_components,
)
from application.import_observations.services.import_observations import (
    ApiImportParameters,
    FileUploadParameters,
    _deduplicate_cross_scanner,
    _process_current_observation,
    _process_new_observation,
    _resolve_unimported_observations,
    api_import_observations,
    file_upload_observations,
)
from application.licenses.models import (
    License,
    License_Component,
    License_Component_Evidence,
    License_Policy,
    License_Policy_Item,
)
from application.licenses.services.license_policy import (
    apply_license_policy_to_component,
)
from application.licenses.types import License_Policy_Evaluation_Result
from application.notifications.types import Webhook_Event_Type
from application.rules.models import Rule
from unittests.base_test_case import BaseTestCase

LICENSES_FILE = "unittests/import_observations/parsers/cyclone_dx/files/licenses_1.json"
CVSS_BT_VECTOR = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"


class TestFileUploadObservations(BaseTestCase):
    def setUp(self):
        Observation.objects.all().delete()
        Observation_Log.objects.all().delete()
        Rule.objects.all().delete()
        Vulnerability_Check.objects.all().delete()
        call_command("loaddata", "unittests/fixtures/import_observations_fixtures.json")
        super().setUp()

    @patch("application.import_observations.services.import_observations.get_subscribed_webhooks")
    @patch("application.import_observations.services.import_observations.emit_observation_event")
    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_emits_created_for_new_active_observations_only(
        self,
        _mock_vex,
        mock_deduplicate_cross_scanner,
        _mock_duplicates,
        _mock_exploit,
        _mock_epss,
        _mock_issue_tracker,
        _mock_security_gate,
        mock_get_current_request,
        mock_emit,
        mock_get_webhooks,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False

        def import_data_1() -> None:
            file_upload_observations(
                FileUploadParameters(
                    product=Product.objects.get(id=1),
                    branch=Branch.objects.get(id=1),
                    file=File(open("unittests/fixtures/data_1/bandit.sarif", "r")),
                    service_name="test_service",
                    docker_image_name_tag="",
                    endpoint_url="",
                    kubernetes_cluster="",
                    kubernetes_namespace="",
                    kubernetes_resource_type="",
                    kubernetes_resource_name="",
                    suppress_licenses=False,
                    sbom=False,
                )
            )

        # 3 new observations, a product rule sets one of them to Not affected
        import_data_1()

        observations = Observation.objects.filter(product=1)
        self.assertEqual(3, observations.count())
        active = {o.pk for o in observations if o.current_status == Status.STATUS_OPEN}
        self.assertEqual(2, len(active))
        self.assertEqual(2, mock_emit.call_count)
        # The webhooks are looked up once per import, not once per observation
        mock_get_webhooks.assert_called_once_with(Webhook_Event_Type.OBSERVATION_CREATED, Product.objects.get(id=1))
        for emit_call in mock_emit.call_args_list:
            self.assertEqual(Webhook_Event_Type.OBSERVATION_CREATED, emit_call.args[0])
            self.assertIs(mock_get_webhooks.return_value, emit_call.args[2])
        self.assertEqual(active, {emit_call.args[1].pk for emit_call in mock_emit.call_args_list})

        # Importing the same file again finds no new observation
        mock_emit.reset_mock()
        import_data_1()

        mock_emit.assert_not_called()

    @patch("application.import_observations.services.import_observations.emit_import_event")
    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_emits_import_completed_once(
        self,
        _mock_vex,
        mock_deduplicate_cross_scanner,
        _mock_duplicates,
        _mock_exploit,
        _mock_epss,
        _mock_issue_tracker,
        _mock_security_gate,
        mock_get_current_request,
        mock_emit_import,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False

        numbers = file_upload_observations(
            FileUploadParameters(
                product=Product.objects.get(id=1),
                branch=Branch.objects.get(id=1),
                file=File(open("unittests/fixtures/data_1/bandit.sarif", "r")),
                service_name="test_service",
                docker_image_name_tag="",
                endpoint_url="",
                kubernetes_cluster="",
                kubernetes_namespace="",
                kubernetes_resource_type="",
                kubernetes_resource_name="",
                suppress_licenses=False,
                sbom=False,
            )
        )

        mock_emit_import.assert_called_once()
        kwargs = mock_emit_import.call_args.kwargs
        self.assertEqual(Product.objects.get(id=1), kwargs["product"])
        self.assertEqual(Branch.objects.get(id=1), kwargs["branch"])
        self.assertEqual("test_service", kwargs["service"].name)
        self.assertEqual("bandit.sarif", kwargs["filename"])
        self.assertEqual("", kwargs["api_configuration_name"])
        self.assertEqual(tuple(numbers[:3]), kwargs["numbers"])
        self.assertTrue(kwargs["parser_name"])

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_with_branch(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False

        self._file_upload_observations(
            Branch.objects.get(id=1),
            "test_service",
            "test_docker_image_name_tag",
            "test_endpoint_url",
            "test_kubernetes_cluster",
            "test_kubernetes_namespace",
            "test_kubernetes_resource_type",
            "test_kubernetes_resource_name",
            False,
        )

        product = Product.objects.get(id=1)
        mock_check_security_gate.assert_has_calls([call(product), call(product)])
        self.assertEqual(mock_push_observations_to_issue_tracker.call_count, 2)
        self.assertEqual(mock_apply_epss.call_count, 4)
        self.assertEqual(mock_apply_exploit_information.call_count, 4)
        self.assertEqual(mock_find_potential_duplicates.call_count, 2)
        self.assertEqual(mock_deduplicate_cross_scanner.call_count, 3)
        self.assertEqual(mock_apply_vex_statements_for_observation.call_count, 4)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_with_branch_cross_scanner_deduplication(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = True

        self._file_upload_observations(
            Branch.objects.get(id=1),
            "test_service",
            "test_docker_image_name_tag",
            "test_endpoint_url",
            "test_kubernetes_cluster",
            "test_kubernetes_namespace",
            "test_kubernetes_resource_type",
            "test_kubernetes_resource_name",
            True,
        )

        product = Product.objects.get(id=1)
        mock_check_security_gate.assert_has_calls([call(product)])
        self.assertEqual(mock_push_observations_to_issue_tracker.call_count, 1)
        self.assertEqual(mock_apply_epss.call_count, 0)
        self.assertEqual(mock_apply_exploit_information.call_count, 0)
        self.assertEqual(mock_find_potential_duplicates.call_count, 1)
        self.assertEqual(mock_deduplicate_cross_scanner.call_count, 3)
        self.assertEqual(mock_apply_vex_statements_for_observation.call_count, 0)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_without_branch(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)
        product.repository_default_branch = None
        product.save()

        self._file_upload_observations(None, None, None, None, None, None, None, None, False)

        mock_check_security_gate.assert_has_calls([call(product), call(product)])
        self.assertEqual(mock_push_observations_to_issue_tracker.call_count, 2)
        self.assertEqual(mock_apply_epss.call_count, 4)
        self.assertEqual(mock_apply_exploit_information.call_count, 4)
        self.assertEqual(mock_find_potential_duplicates.call_count, 2)
        self.assertEqual(mock_deduplicate_cross_scanner.call_count, 3)
        self.assertEqual(mock_apply_vex_statements_for_observation.call_count, 4)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_different_branch(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._file_upload_observations(None, None, None, None, None, None, None, None, False)

        mock_check_security_gate.assert_not_called()
        self.assertEqual(mock_push_observations_to_issue_tracker.call_count, 2)
        self.assertEqual(mock_apply_epss.call_count, 4)
        self.assertEqual(mock_apply_exploit_information.call_count, 4)
        self.assertEqual(mock_find_potential_duplicates.call_count, 2)
        self.assertEqual(mock_deduplicate_cross_scanner.call_count, 3)
        self.assertEqual(mock_apply_vex_statements_for_observation.call_count, 4)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_skip_resolved(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")
        statuses_first_import = dict(Observation.objects.filter(product=product).values_list("id", "current_status"))
        self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")
        resolved_before = list(
            Observation.objects.filter(product=product, current_status=Status.STATUS_RESOLVED)
            .order_by("id")
            .values_list("id", "modified")
        )
        self.assertEqual(len(resolved_before), 2)

        self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        self.assertEqual(Observation_Log.objects.filter(observation__product=product).count(), 7)
        resolved_after = list(
            Observation.objects.filter(pk__in=[pk for pk, _ in resolved_before])
            .order_by("id")
            .values_list("id", "modified")
        )
        self.assertEqual(resolved_before, resolved_after)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")

        for observation in Observation.objects.filter(pk__in=[pk for pk, _ in resolved_before]):
            self.assertEqual(observation.current_status, statuses_first_import[observation.pk])

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_one_save_per_observation(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        observation_updates = [
            query["sql"] for query in context.captured_queries if query["sql"].startswith('UPDATE "core_observation"')
        ]
        # One for the observation with the changed severity and one for each of the two resolved observations
        self.assertEqual(len(observation_updates), 3)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_unchanged_only_import_last_seen(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")

        observation_updates = [
            query["sql"] for query in context.captured_queries if query["sql"].startswith('UPDATE "core_observation"')
        ]
        self.assertTrue(observation_updates)
        for observation_update in observation_updates:
            self.assertTrue(
                observation_update.startswith('UPDATE "core_observation" SET "import_last_seen" = '),
                observation_update,
            )
            self.assertNotIn('"modified"', observation_update)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_changed_fields_and_modified(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")
        observation_ids = list(Observation.objects.filter(product=product).values_list("pk", flat=True))
        Observation.objects.filter(pk__in=observation_ids).update(description="old description")
        modified_before = {
            observation.pk: observation.modified for observation in Observation.objects.filter(pk__in=observation_ids)
        }

        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")

        observation_updates = [
            query["sql"] for query in context.captured_queries if query["sql"].startswith('UPDATE "core_observation"')
        ]
        self.assertEqual(len(observation_updates), len(observation_ids))
        for observation_update in observation_updates:
            self.assertIn('"description" = ', observation_update)
            self.assertIn('"import_last_seen" = ', observation_update)
            self.assertIn('"modified" = ', observation_update)
            self.assertNotIn('"title" = ', observation_update)

        for observation in Observation.objects.filter(pk__in=observation_ids):
            self.assertNotEqual("old description", observation.description)
            self.assertGreater(observation.modified, modified_before[observation.pk])

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_docker_image_tag_updated(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif", "registry.example.com/app:1.0")
        observation_ids = list(Observation.objects.filter(product=product).order_by("id").values_list("pk", flat=True))
        self.assertEqual(3, len(observation_ids))

        numbers = self._import_file(product, "unittests/fixtures/data_1/bandit.sarif", "registry.example.com/app:2.0")

        self.assertEqual((0, 2, 0), numbers[:3])
        observations = Observation.objects.filter(product=product).order_by("id")
        self.assertEqual(observation_ids, [observation.pk for observation in observations])
        for observation in observations:
            self.assertEqual("registry.example.com/app", observation.origin_docker_image_name)
            self.assertEqual("2.0", observation.origin_docker_image_tag)
            self.assertEqual("registry.example.com/app:2.0", observation.origin_docker_image_name_tag)
            self.assertEqual("app:2.0", observation.origin_docker_image_name_tag_short)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_docker_image_tag_updated_with_log(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif", "registry.example.com/app:1.0")
        self._import_file(product, "unittests/fixtures/data_2/bandit.sarif", "registry.example.com/app:2.0")

        # The resolved observations keep the last image they have been found in,
        # the one with the changed severity is saved by the observation log
        self.assertEqual(
            [(Status.STATUS_RESOLVED, "1.0"), (Status.STATUS_OPEN, "2.0"), (Status.STATUS_RESOLVED, "1.0")],
            list(
                Observation.objects.filter(product=product)
                .order_by("id")
                .values_list("current_status", "origin_docker_image_tag")
            ),
        )

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    @patch("application.import_observations.parsers.sarif.parser.SARIFParser.get_observations")
    def test_file_upload_observations_docker_image_tag_changes_identity_hash(
        self,
        mock_get_observations,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        def imported_observations(tag):
            return [
                Observation(
                    title="docker_observation",
                    parser_severity=Severity.SEVERITY_HIGH,
                    origin_docker_image_name="registry.example.com/app",
                    origin_docker_image_tag=tag,
                )
            ], "scanner"

        mock_get_observations.side_effect = [imported_observations("1.0"), imported_observations("sha256:abc")]

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif", "")
        # A tag with a colon becomes part of the name when the observation is saved and changes its identity hash
        numbers = self._import_file(product, "unittests/fixtures/data_1/bandit.sarif", "")

        self.assertEqual((0, 1, 0), numbers[:3])
        observation = Observation.objects.get(product=product)
        self.assertEqual("registry.example.com/app:sha256:abc", observation.origin_docker_image_name_tag)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_product_timestamp_only(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        product_updates = [
            query["sql"] for query in context.captured_queries if query["sql"].startswith('UPDATE "core_product"')
        ]
        self.assertTrue(product_updates)
        for product_update in product_updates:
            self.assertTrue(
                product_update.startswith('UPDATE "core_product" SET "last_observation_change" = '), product_update
            )
        self.assertNotIn("last_observation_change", product.get_dirty_fields())

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_product_written_once(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")

        # The newest log of the first import comes from a product rule, which must not bypass the deferred timestamp
        latest_observation_log = Observation_Log.objects.filter(observation__product=product).latest("created")
        self.assertIsNotNone(latest_observation_log.product_rule)
        product.refresh_from_db()
        self.assertEqual(product.last_observation_change, latest_observation_log.created)

        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        self.assertEqual(len(self._product_updates(context)), 1)
        product.refresh_from_db()
        self.assertEqual(
            product.last_observation_change,
            Observation_Log.objects.filter(observation__product=product).latest("created").created,
        )

        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        self.assertEqual(len(self._product_updates(context)), 0)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    @patch("application.import_observations.services.import_observations.transaction")
    def test_file_upload_observations_product_written_per_log_without_transaction(
        self,
        mock_transaction,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_transaction.get_autocommit.return_value = True
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        # One for the observation with the changed severity and one for each of the two resolved observations
        product_updates = self._product_updates(context)
        self.assertEqual(len(product_updates), 3)
        for product_update in product_updates:
            self.assertTrue(
                product_update.startswith('UPDATE "core_product" SET "last_observation_change" = '), product_update
            )

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.import_observations.services.import_observations._deduplicate_cross_scanner")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_observations_references_and_evidences_queries(
        self,
        mock_apply_vex_statements_for_observation,
        mock_deduplicate_cross_scanner,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        mock_deduplicate_cross_scanner.return_value = False
        product = Product.objects.get(id=1)

        # New observations: nothing to compare with, only inserted
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")

        for table in ["core_reference", "core_evidence"]:
            self.assertEqual(len(self._table_queries(context, "SELECT", table)), 0, table)
            self.assertEqual(len(self._table_queries(context, "DELETE", table)), 0, table)
            self.assertTrue(self._table_queries(context, "INSERT", table), table)

        references_before = list(Reference.objects.filter(observation__product=product).values_list("id", "url"))
        evidences_before = list(Evidence.objects.filter(observation__product=product).values_list("id", "evidence"))
        self.assertTrue(references_before)
        self.assertTrue(evidences_before)

        # Unchanged observations: one prefetch for all of them, nothing rewritten
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_1/bandit.sarif")

        for table in ["core_reference", "core_evidence"]:
            self.assertEqual(len(self._table_queries(context, "SELECT", table)), 1, table)
            self.assertEqual(len(self._table_queries(context, "DELETE", table)), 0, table)
            self.assertEqual(len(self._table_queries(context, "INSERT", table)), 0, table)

        evidence_select = self._table_queries(context, "SELECT", "core_evidence")[0]
        # Only the hash of the evidence is read, not the evidence itself
        self.assertNotIn('"core_evidence"."evidence",', evidence_select)
        self.assertNotIn('"core_evidence"."evidence" FROM', evidence_select)
        self.assertIn('MD5("core_evidence"."evidence")', evidence_select)
        self.assertEqual(
            references_before,
            list(Reference.objects.filter(observation__product=product).values_list("id", "url")),
        )
        self.assertEqual(
            evidences_before,
            list(Evidence.objects.filter(observation__product=product).values_list("id", "evidence")),
        )

        # Changed and resolved observations: still one prefetch for all of them
        with CaptureQueriesContext(connection) as context:
            self._import_file(product, "unittests/fixtures/data_2/bandit.sarif")

        for table in ["core_reference", "core_evidence"]:
            self.assertEqual(len(self._table_queries(context, "SELECT", table)), 1, table)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_licenses_unchanged_queries(
        self,
        mock_apply_vex_statements_for_observation,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        product = self._prepare_license_import()

        self._import_file(product, LICENSES_FILE)
        components_before = self._license_components(product)
        evidences_before = self._license_evidences(product)
        self.assertEqual(67, len(components_before))
        self.assertEqual(67, len(evidences_before))

        with CaptureQueriesContext(connection) as context:
            numbers = self._import_file(product, LICENSES_FILE)

        self.assertEqual((0, 67, 0), numbers[3:])

        # The core components are only needed for new license components
        self.assertEqual(0, len(self._table_queries(context, "SELECT", "core_component")))
        self.assertEqual(0, len(self._table_queries(context, "INSERT", "core_component")))

        # Evidences are compared by their hash, nothing is rewritten
        evidence_table = "licenses_license_component_evidence"
        self.assertEqual(1, len(self._table_queries(context, "SELECT", evidence_table)))
        self.assertEqual(0, len(self._table_queries(context, "DELETE", evidence_table)))
        self.assertEqual(0, len(self._table_queries(context, "INSERT", evidence_table)))
        self.assertIn(
            'MD5("licenses_license_component_evidence"."evidence")',
            self._table_queries(context, "SELECT", evidence_table)[0],
        )

        # Unchanged components only get a new import_last_seen
        component_updates = self._license_component_updates(context)
        self.assertEqual(1, len(component_updates))
        self.assertTrue(
            component_updates[0].startswith('UPDATE "licenses_license_component" SET "import_last_seen" = '),
            component_updates[0],
        )

        components_after = self._license_components(product)
        self.assertEqual(evidences_before, self._license_evidences(product))
        for component_before, component_after in zip(components_before, components_after):
            self.assertEqual(component_before["id"], component_after["id"])
            self.assertEqual(component_before["last_change"], component_after["last_change"])
            self.assertEqual(component_before["evaluation_result"], component_after["evaluation_result"])
            self.assertGreater(component_after["import_last_seen"], component_before["import_last_seen"])

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_licenses_changed(
        self,
        mock_apply_vex_statements_for_observation,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))
        product = self._prepare_license_import()

        self._import_file(product, LICENSES_FILE)
        components_before = {c["component_name"]: c for c in self._license_components(product)}
        evidences_before = self._license_evidences(product)

        with open(LICENSES_FILE, "r") as file:
            sbom = json.load(file)
        for component in sbom["components"]:
            if component["name"] == "argon2-cffi":
                # Changed license
                component["licenses"] = [{"license": {"id": "Apache-2.0"}}]
            if component["name"] == "CacheControl":
                # Only the evidence changes
                component["description"] = "changed description"

        with tempfile.TemporaryDirectory() as directory:
            # Same file name, to update the same vulnerability check
            changed_file = os.path.join(directory, os.path.basename(LICENSES_FILE))
            with open(changed_file, "w") as file:
                json.dump(sbom, file)

            with CaptureQueriesContext(connection) as context:
                numbers = self._import_file(product, changed_file)

        self.assertEqual((0, 67, 0), numbers[3:])

        components_after = {c["component_name"]: c for c in self._license_components(product)}
        evidences_after = self._license_evidences(product)

        argon2_before = components_before["argon2-cffi"]
        argon2_after = components_after["argon2-cffi"]
        self.assertEqual("MIT", argon2_before["effective_license_name"])
        self.assertEqual("Apache-2.0", argon2_after["effective_license_name"])
        self.assertGreater(argon2_after["last_change"], argon2_before["last_change"])
        # The evidence contains the license as well
        self.assertNotEqual(evidences_before[argon2_before["id"]], evidences_after[argon2_after["id"]])

        cache_control_before = components_before["CacheControl"]
        cache_control_after = components_after["CacheControl"]
        self.assertEqual(cache_control_before["last_change"], cache_control_after["last_change"])
        self.assertNotEqual(evidences_before[cache_control_before["id"]], evidences_after[cache_control_after["id"]])
        self.assertIn("changed description", evidences_after[cache_control_after["id"]][0][1])

        for name, component_before in components_before.items():
            if name not in ["argon2-cffi", "CacheControl"]:
                self.assertEqual(component_before["last_change"], components_after[name]["last_change"], name)
                self.assertEqual(evidences_before[component_before["id"]], evidences_after[component_before["id"]])

        # Only the two changed evidences are replaced
        evidence_table = "licenses_license_component_evidence"
        self.assertEqual(1, len(self._table_queries(context, "DELETE", evidence_table)))
        self.assertEqual(1, len(self._table_queries(context, "INSERT", evidence_table)))
        changed_evidences = [
            component_id
            for component_id, evidences in evidences_after.items()
            if evidences != evidences_before[component_id]
        ]
        self.assertEqual(sorted([argon2_after["id"], cache_control_after["id"]]), sorted(changed_evidences))

    def _prepare_license_import(self):
        try:
            License_Policy.objects.get(name="Standard")
        except License_Policy.DoesNotExist:
            call_command("loaddata", "unittests/fixtures/initial_license_data.json")

        settings = Settings.load()
        settings.feature_license_management = True
        settings.save()

        License_Component.objects.all().delete()
        return Product.objects.get(id=1)

    def _license_components(self, product):
        return list(
            License_Component.objects.filter(product=product)
            .order_by("id")
            .values(
                "id", "component_name", "effective_license_name", "evaluation_result", "last_change", "import_last_seen"
            )
        )

    def _license_evidences(self, product):
        evidences = {}
        for license_component_id, evidence_id, evidence in (
            License_Component_Evidence.objects.filter(license_component__product=product)
            .order_by("id")
            .values_list("license_component_id", "id", "evidence")
        ):
            evidences.setdefault(license_component_id, []).append((evidence_id, evidence))
        return evidences

    def _license_component_updates(self, context):
        return [
            query["sql"]
            for query in context.captured_queries
            if query["sql"].startswith('UPDATE "licenses_license_component"')
        ]

    def _table_queries(self, context, statement, table):
        prefixes = {
            "SELECT": "SELECT ",
            "DELETE": f'DELETE FROM "{table}"',
            "INSERT": f'INSERT INTO "{table}"',
        }
        return [
            query["sql"]
            for query in context.captured_queries
            if query["sql"].startswith(prefixes[statement])
            and (statement != "SELECT" or f'FROM "{table}"' in query["sql"])
        ]

    def _product_updates(self, context):
        return [query["sql"] for query in context.captured_queries if query["sql"].startswith('UPDATE "core_product"')]

    def _import_file(self, product, file_name, docker_image_name_tag="test_docker_image_name_tag"):
        with open(file_name, "r") as file:
            return file_upload_observations(
                FileUploadParameters(
                    product=product,
                    branch=Branch.objects.get(id=1),
                    file=File(file),
                    service_name="test_service",
                    docker_image_name_tag=docker_image_name_tag,
                    endpoint_url="test_endpoint_url",
                    kubernetes_cluster="test_kubernetes_cluster",
                    kubernetes_namespace="test_kubernetes_namespace",
                    kubernetes_resource_type="test_kubernetes_resource_type",
                    kubernetes_resource_name="test_kubernetes_resource_name",
                    suppress_licenses=False,
                    sbom=False,
                )
            )

    def _file_upload_observations(
        self,
        branch,
        service_name,
        docker_image_name_tag,
        endpoint_url,
        kubernetes_cluster,
        kubernetes_namespace,
        kubernetes_resource_type,
        kubernetes_resource_name,
        deduplicate_cross_scanner,
    ):
        # --- First import ---

        file_upload_parameters = FileUploadParameters(
            product=Product.objects.get(id=1),
            branch=branch,
            file=File(open("unittests/fixtures/data_1/bandit.sarif", "r")),
            service_name=service_name,
            docker_image_name_tag=docker_image_name_tag,
            endpoint_url=endpoint_url,
            kubernetes_cluster=kubernetes_cluster,
            kubernetes_namespace=kubernetes_namespace,
            kubernetes_resource_type=kubernetes_resource_type,
            kubernetes_resource_name=kubernetes_resource_name,
            suppress_licenses=False,
            sbom=False,
        )

        (
            new_observations,
            updated_observations,
            resolved_observations,
            new_license_objects,
            updated_license_objects,
            deleted_license_objects,
        ) = file_upload_observations(file_upload_parameters)

        if deduplicate_cross_scanner:
            self.assertEqual(new_observations, 0)
        else:
            self.assertEqual(new_observations, 2)
        self.assertEqual(updated_observations, 0)
        self.assertEqual(resolved_observations, 0)
        self.assertEqual(new_license_objects, 0)
        self.assertEqual(updated_license_objects, 0)
        self.assertEqual(deleted_license_objects, 0)

        product = Product.objects.get(id=1)

        observations = Observation.objects.filter(product=1).order_by("id")
        if deduplicate_cross_scanner:
            self.assertEqual(len(observations), 0)
        else:
            self.assertEqual(len(observations), 3)

        if deduplicate_cross_scanner:
            return

        self.assertEqual(observations[0].product, product)
        self.assertEqual(observations[0].branch, branch)
        service = None
        if service_name:
            service = Service.objects.get(product=product, name=service_name)
            self.assertEqual(observations[0].origin_service, service)
        else:
            self.assertIsNone(observations[0].origin_service)
        if docker_image_name_tag:
            self.assertEqual(observations[0].origin_docker_image_name_tag, docker_image_name_tag)
        else:
            self.assertEqual(observations[0].origin_docker_image_name_tag, "")
        if endpoint_url:
            self.assertEqual(observations[0].origin_endpoint_url, endpoint_url)
        else:
            self.assertEqual(observations[0].origin_endpoint_url, "")
        if kubernetes_cluster:
            self.assertEqual(observations[0].origin_kubernetes_cluster, kubernetes_cluster)
        else:
            self.assertEqual(observations[0].origin_kubernetes_cluster, "")
        if kubernetes_namespace:
            self.assertEqual(observations[0].origin_kubernetes_namespace, kubernetes_namespace)
        else:
            self.assertEqual(observations[0].origin_kubernetes_namespace, "")
        if kubernetes_resource_type:
            self.assertEqual(observations[0].origin_kubernetes_resource_type, kubernetes_resource_type)
        else:
            self.assertEqual(observations[0].origin_kubernetes_resource_type, "")
        if kubernetes_resource_name:
            self.assertEqual(observations[0].origin_kubernetes_resource_name, kubernetes_resource_name)
        else:
            self.assertEqual(observations[0].origin_kubernetes_resource_name, "")

        self.assertEqual(observations[0].current_status, Status.STATUS_OPEN)
        self.assertEqual(observations[1].current_status, Status.STATUS_OPEN)
        self.assertEqual(observations[2].current_status, Status.STATUS_NOT_AFFECTED)

        observation_logs = Observation_Log.objects.filter(observation__product=1).order_by("id")
        self.assertEqual(len(observation_logs), 4)

        self.assertEqual(observation_logs[0].observation, observations[0])
        self.assertEqual(observation_logs[1].observation, observations[1])

        self.assertEqual(observation_logs[2].observation, observations[2])
        self.assertEqual(observation_logs[2].severity, observations[2].current_severity)
        self.assertEqual(observation_logs[2].status, Status.STATUS_OPEN)
        self.assertEqual(observation_logs[2].comment, "Set by parser")

        self.assertEqual(observation_logs[3].observation, observations[2])
        self.assertEqual(observation_logs[3].severity, "")
        self.assertEqual(observation_logs[3].status, observations[2].current_status)
        self.assertEqual(
            observation_logs[3].comment,
            "Updated by product rule db_product_rule_import",
        )

        references = Reference.objects.filter(observation__product=product).order_by("id")
        self.assertEqual(len(references), 3)

        self.assertEqual(references[0].observation, observations[0])
        self.assertEqual(
            references[0].url,
            "https://bandit.readthedocs.io/en/1.7.4/plugins/b104_hardcoded_bind_all_interfaces.html",
        )

        evidences = Evidence.objects.filter(observation__product=product).order_by("id")
        self.assertEqual(len(evidences), 6)

        vulnerability_checks = Vulnerability_Check.objects.filter(product=1)
        self.assertEqual(len(vulnerability_checks), 1)

        self.assertEqual(vulnerability_checks[0].product, product)
        self.assertEqual(vulnerability_checks[0].branch, branch)
        self.assertEqual(vulnerability_checks[0].service, service)
        self.assertEqual(vulnerability_checks[0].filename, "bandit.sarif")
        self.assertEqual(vulnerability_checks[0].api_configuration_name, "")
        self.assertEqual(vulnerability_checks[0].scanner, "Bandit")
        self.assertEqual(vulnerability_checks[0].last_import_observations_new, 2)
        self.assertEqual(vulnerability_checks[0].last_import_observations_updated, 0)
        self.assertEqual(vulnerability_checks[0].last_import_observations_resolved, 0)

        # --- Second import with some changes ---

        file_upload_parameters = FileUploadParameters(
            product=Product.objects.get(id=1),
            branch=branch,
            file=File(open("unittests/fixtures/data_2/bandit.sarif", "r")),
            service_name=service_name,
            docker_image_name_tag=docker_image_name_tag,
            endpoint_url=endpoint_url,
            kubernetes_cluster=kubernetes_cluster,
            kubernetes_namespace=kubernetes_namespace,
            kubernetes_resource_type=kubernetes_resource_type,
            kubernetes_resource_name=kubernetes_resource_name,
            suppress_licenses=False,
            sbom=False,
        )

        (
            new_observations,
            updated_observations,
            resolved_observations,
            new_license_objects,
            updated_license_objects,
            deleted_license_objects,
        ) = file_upload_observations(file_upload_parameters)

        self.assertEqual(new_observations, 0)
        self.assertEqual(updated_observations, 1)
        self.assertEqual(resolved_observations, 1)
        self.assertEqual(new_license_objects, 0)
        self.assertEqual(updated_license_objects, 0)
        self.assertEqual(deleted_license_objects, 0)

        observations = Observation.objects.filter(product=1).order_by("id")
        self.assertEqual(len(observations), 3)

        self.assertEqual(observations[0].current_status, Status.STATUS_RESOLVED)
        self.assertEqual(observations[1].current_status, Status.STATUS_OPEN)
        self.assertEqual(observations[2].current_status, Status.STATUS_RESOLVED)

        observation_logs = Observation_Log.objects.filter(observation__product=1).order_by("id")
        self.assertEqual(len(observation_logs), 7)

        self.assertEqual(observation_logs[4].observation, observations[1])
        self.assertEqual(observation_logs[4].severity, Severity.SEVERITY_HIGH)
        self.assertEqual(observation_logs[4].status, "")
        self.assertEqual(observation_logs[4].comment, "Updated by parser")

        self.assertEqual(observation_logs[5].observation, observations[0])
        self.assertEqual(observation_logs[5].severity, "")
        self.assertEqual(observation_logs[5].status, Status.STATUS_RESOLVED)
        self.assertEqual(observation_logs[5].comment, "Observation not found in latest scan")

        self.assertEqual(observation_logs[6].observation, observations[2])
        self.assertEqual(observation_logs[6].severity, "")
        self.assertEqual(observation_logs[6].status, Status.STATUS_RESOLVED)
        self.assertEqual(observation_logs[6].comment, "Observation not found in latest scan")

        references = Reference.objects.filter(observation__product=product).order_by("id")
        self.assertEqual(len(references), 3)

        evidences = Evidence.objects.filter(observation__product=product).order_by("id")
        self.assertEqual(len(evidences), 6)

        vulnerability_checks = Vulnerability_Check.objects.filter(product=1)
        self.assertEqual(len(vulnerability_checks), 1)

        self.assertEqual(vulnerability_checks[0].product, product)
        self.assertEqual(vulnerability_checks[0].branch, branch)
        self.assertEqual(vulnerability_checks[0].service, service)
        self.assertEqual(vulnerability_checks[0].filename, "bandit.sarif")
        self.assertEqual(vulnerability_checks[0].api_configuration_name, "")
        self.assertEqual(vulnerability_checks[0].scanner, "Bandit")
        self.assertEqual(vulnerability_checks[0].last_import_observations_new, 0)
        self.assertEqual(vulnerability_checks[0].last_import_observations_updated, 1)
        self.assertEqual(vulnerability_checks[0].last_import_observations_resolved, 1)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    @patch("application.import_observations.parsers.cyclone_dx.parser.CycloneDXParser.get_license_components")
    @patch("application.import_observations.services.import_observations.process_license_components")
    def test_file_upload_licenses_feature_false(
        self,
        mock_process_license_components,
        mock_get_license_components,
        mock_apply_vex_statements_for_observation,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))

        settings = Settings.load()
        settings.feature_license_management = False
        settings.save()

        self._file_upload_licenses(
            Branch.objects.get(id=1),
            "test_service",
            "test_docker_image_name_tag",
            "test_endpoint_url",
            "test_kubernetes_cluster",
            "test_kubernetes_namespace",
            "test_kubernetes_resource_type",
            "test_kubernetes_resource_name",
            suppress_licenses=False,
            sbom=True,
        )

        self.assertEqual(mock_get_license_components.call_count, 0)
        self.assertEqual(mock_process_license_components.call_count, 0)

        settings = Settings.load()
        settings.feature_license_management = True
        settings.save()

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    @patch("application.import_observations.parsers.cyclone_dx.parser.CycloneDXParser.get_license_components")
    @patch("application.import_observations.services.import_observations.process_license_components")
    def test_file_upload_suppress_licenses_true(
        self,
        mock_process_license_components,
        mock_get_license_components,
        mock_apply_vex_statements_for_observation,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))

        self._file_upload_licenses(
            Branch.objects.get(id=1),
            "test_service",
            "test_docker_image_name_tag",
            "test_endpoint_url",
            "test_kubernetes_cluster",
            "test_kubernetes_namespace",
            "test_kubernetes_resource_type",
            "test_kubernetes_resource_name",
            suppress_licenses=True,
            sbom=False,
        )

        self.assertEqual(mock_get_license_components.call_count, 0)
        self.assertEqual(mock_process_license_components.call_count, 0)

    @patch("application.commons.services.global_request.get_current_request")
    @patch("application.import_observations.services.import_observations.check_security_gate")
    @patch("application.import_observations.services.import_observations.push_observations_to_issue_tracker")
    @patch("application.import_observations.services.import_observations.apply_epss")
    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.find_potential_duplicates")
    @patch("application.vex.services.vex_engine.VEX_Engine.apply_vex_statements_for_observation")
    def test_file_upload_licenses_feature_true(
        self,
        mock_apply_vex_statements_for_observation,
        mock_find_potential_duplicates,
        mock_apply_exploit_information,
        mock_apply_epss,
        mock_push_observations_to_issue_tracker,
        mock_check_security_gate,
        mock_get_current_request,
    ):
        mock_get_current_request.return_value = RequestMock(User.objects.get(id=1))

        settings = Settings.load()
        settings.feature_license_management = True
        settings.save()

        self._file_upload_licenses(
            Branch.objects.get(id=1),
            "test_service",
            "test_docker_image_name_tag",
            "test_endpoint_url",
            "test_kubernetes_cluster",
            "test_kubernetes_namespace",
            "test_kubernetes_resource_type",
            "test_kubernetes_resource_name",
            suppress_licenses=False,
            sbom=True,
        )

    def _file_upload_licenses(
        self,
        branch,
        service,
        docker_image_name_tag,
        endpoint_url,
        kubernetes_cluster,
        kubernetes_namespace,
        kubernetes_resource_type,
        kubernetes_resource_name,
        suppress_licenses,
        sbom,
    ):
        try:
            license_policy_standard = License_Policy.objects.get(name="Standard")
        except License_Policy.DoesNotExist:
            call_command("loaddata", "unittests/fixtures/initial_license_data.json")
            license_policy_standard = License_Policy.objects.get(name="Standard")

        License_Component.objects.all().delete()

        # --- First import without license policy ---

        file_upload_parameters = FileUploadParameters(
            product=Product.objects.get(id=1),
            branch=branch,
            file=File(
                open(
                    "unittests/import_observations/parsers/cyclone_dx/files/licenses_1.json",
                    "r",
                )
            ),
            service_name=service,
            docker_image_name_tag=docker_image_name_tag,
            endpoint_url=endpoint_url,
            kubernetes_cluster=kubernetes_cluster,
            kubernetes_namespace=kubernetes_namespace,
            kubernetes_resource_type=kubernetes_resource_type,
            kubernetes_resource_name=kubernetes_resource_name,
            suppress_licenses=suppress_licenses,
            sbom=sbom,
        )

        (
            new_observations,
            updated_observations,
            resolved_observations,
            new_license_objects,
            updated_license_objects,
            deleted_license_objects,
        ) = file_upload_observations(file_upload_parameters)

        settings = Settings.load()
        if settings.feature_license_management and not suppress_licenses:
            self.assertEqual(new_observations, 0)
            self.assertEqual(updated_observations, 0)
            self.assertEqual(resolved_observations, 0)
            self.assertEqual(new_license_objects, 67)
            self.assertEqual(updated_license_objects, 0)
            self.assertEqual(deleted_license_objects, 0)

            license_components = License_Component.objects.filter(product=1).order_by("id")
            self.assertEqual(len(license_components), 67)

            self.assertEqual(license_components[1].branch, branch)
            self.assertEqual(license_components[1].upload_filename, "licenses_1.json")
            self.assertEqual(license_components[1].component_name, "argon2-cffi-bindings")
            self.assertEqual(license_components[1].component_version, "21.2.0")
            self.assertEqual(
                license_components[1].component_name_version,
                "argon2-cffi-bindings:21.2.0",
            )
            self.assertEqual(
                license_components[1].component_purl,
                "pkg:pypi/argon2-cffi-bindings@21.2.0",
            )
            self.assertEqual(license_components[1].component_purl_type, "pypi")
            self.assertEqual(license_components[1].component_cpe, "")
            dependencies = """SecObserve:1.66.0 --> argon2-cffi:23.1.0
argon2-cffi:23.1.0 --> argon2-cffi-bindings:21.2.0"""
            self.assertEqual(license_components[1].component_dependencies, dependencies)
            self.assertEqual(license_components[1].effective_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[1].effective_license_name, "MIT")
            self.assertEqual(license_components[1].imported_declared_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[1].imported_declared_license_name, "MIT")
            self.assertEqual(
                license_components[1].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            )
            self.assertEqual(
                license_components[1].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_UNKNOWN,
                ),
            )

            self.assertEqual(license_components[3].component_name_version, "asgiref:3.8.1")
            self.assertEqual(license_components[3].effective_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[3].effective_license_name, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[3].imported_declared_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[3].imported_declared_license_name, "0BSD, BSD-3-Clause")
            self.assertEqual(
                license_components[3].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            )
            self.assertEqual(
                license_components[3].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_UNKNOWN,
                ),
            )

            self.assertEqual(license_components[4].component_name_version, "attrs:24.2.0")
            self.assertEqual(license_components[4].effective_non_spdx_license, "attrs non-standard license")
            self.assertEqual(license_components[4].effective_license_name, "attrs non-standard license")
            self.assertEqual(license_components[4].imported_declared_non_spdx_license, "attrs non-standard license")
            self.assertEqual(license_components[4].imported_declared_license_name, "attrs non-standard license")
            self.assertEqual(
                license_components[4].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            )
            self.assertEqual(
                license_components[4].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_UNKNOWN,
                ),
            )

            self.assertEqual(license_components[24].component_name_version, "email-validator:2.1.1")
            self.assertEqual(
                license_components[24].effective_license_expression,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].effective_license_name,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].imported_declared_license_expression,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].imported_declared_license_name,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            )
            self.assertEqual(
                license_components[24].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_UNKNOWN,
                ),
            )

        # --- Second import with license policy ---

        product = Product.objects.get(id=1)
        product.license_policy = license_policy_standard
        product.save()

        license_policy_item = License_Policy_Item(
            license_policy=license_policy_standard,
            license_group=None,
            license=None,
            license_expression="GPL-2.0-or-later WITH Bison-exception-2.2",
            non_spdx_license="",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        )
        license_policy_item.save()

        file_upload_parameters = FileUploadParameters(
            product=product,
            branch=branch,
            file=File(
                open(
                    "unittests/import_observations/parsers/cyclone_dx/files/licenses_1.json",
                    "r",
                )
            ),
            service_name=service,
            docker_image_name_tag=docker_image_name_tag,
            endpoint_url=endpoint_url,
            kubernetes_cluster=kubernetes_cluster,
            kubernetes_namespace=kubernetes_namespace,
            kubernetes_resource_type=kubernetes_resource_type,
            kubernetes_resource_name=kubernetes_resource_name,
            suppress_licenses=suppress_licenses,
            sbom=sbom,
        )

        (
            new_observations,
            updated_observations,
            resolved_observations,
            new_license_objects,
            updated_license_objects,
            deleted_license_objects,
        ) = file_upload_observations(file_upload_parameters)

        settings = Settings.load()
        if settings.feature_license_management and not suppress_licenses:
            self.assertEqual(new_observations, 0)
            self.assertEqual(updated_observations, 0)
            self.assertEqual(resolved_observations, 0)
            self.assertEqual(new_license_objects, 0)
            self.assertEqual(updated_license_objects, 67)
            self.assertEqual(deleted_license_objects, 0)

            license_components = License_Component.objects.filter(product=1).order_by("id")
            self.assertEqual(len(license_components), 67)

            self.assertEqual(
                license_components[1].component_name_version,
                "argon2-cffi-bindings:21.2.0",
            )
            self.assertEqual(license_components[1].effective_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[1].effective_license_name, "MIT")
            self.assertEqual(license_components[1].imported_declared_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[1].imported_declared_license_name, "MIT")
            self.assertEqual(
                license_components[1].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_ALLOWED,
            )
            self.assertEqual(
                license_components[1].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_ALLOWED,
                ),
            )

            self.assertEqual(license_components[3].component_name_version, "asgiref:3.8.1")
            self.assertEqual(license_components[3].effective_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[3].effective_license_name, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[3].imported_declared_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[3].imported_declared_license_name, "0BSD, BSD-3-Clause")
            self.assertEqual(
                license_components[3].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_ALLOWED,
            )
            self.assertEqual(
                license_components[3].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_ALLOWED,
                ),
            )

            self.assertEqual(license_components[4].component_name_version, "attrs:24.2.0")
            self.assertEqual(license_components[4].effective_non_spdx_license, "attrs non-standard license")
            self.assertEqual(license_components[4].effective_license_name, "attrs non-standard license")
            self.assertEqual(license_components[4].imported_declared_non_spdx_license, "attrs non-standard license")
            self.assertEqual(license_components[4].imported_declared_license_name, "attrs non-standard license")
            self.assertEqual(
                license_components[4].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            )
            self.assertEqual(
                license_components[4].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_UNKNOWN,
                ),
            )

            self.assertEqual(license_components[9].component_name_version, "cryptography:43.0.1")
            self.assertEqual(
                license_components[9].effective_license_expression,
                "LGPL-3.0-or-later OR BSD-3-Clause",
            )
            self.assertEqual(
                license_components[9].effective_license_name,
                "LGPL-3.0-or-later OR BSD-3-Clause",
            )
            self.assertEqual(
                license_components[9].imported_declared_license_expression, "LGPL-3.0-or-later OR BSD-3-Clause"
            )
            self.assertEqual(license_components[9].imported_declared_license_name, "LGPL-3.0-or-later OR BSD-3-Clause")
            self.assertEqual(
                license_components[9].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_ALLOWED,
            )
            self.assertEqual(
                license_components[9].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_ALLOWED,
                ),
            )

            self.assertEqual(license_components[10].component_name_version, "cvss:3.2")
            self.assertEqual(
                license_components[10].effective_license_expression,
                "GPL-3.0-or-later AND BSD-3-Clause",
            )
            self.assertEqual(
                license_components[10].effective_license_name,
                "GPL-3.0-or-later AND BSD-3-Clause",
            )
            self.assertEqual(
                license_components[10].imported_declared_license_expression, "GPL-3.0-or-later AND BSD-3-Clause"
            )
            self.assertEqual(license_components[10].imported_declared_license_name, "GPL-3.0-or-later AND BSD-3-Clause")
            self.assertEqual(
                license_components[10].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            )
            self.assertEqual(
                license_components[10].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                ),
            )

            self.assertEqual(license_components[11].component_name_version, "defusedcsv:2.0.0")
            self.assertEqual(
                license_components[11].effective_license_expression,
                "(Apache-2.0 OR BSD-3-Clause) AND MIT",
            )
            self.assertEqual(
                license_components[11].effective_license_name,
                "(Apache-2.0 OR BSD-3-Clause) AND MIT",
            )
            self.assertEqual(
                license_components[11].imported_declared_license_expression,
                "(Apache-2.0 OR BSD-3-Clause) AND MIT",
            )
            self.assertEqual(
                license_components[11].imported_declared_license_name,
                "(Apache-2.0 OR BSD-3-Clause) AND MIT",
            )
            self.assertEqual(
                license_components[11].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_ALLOWED,
            )
            self.assertEqual(
                license_components[11].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_ALLOWED,
                ),
            )

            self.assertEqual(license_components[24].component_name_version, "email-validator:2.1.1")
            self.assertEqual(
                license_components[24].effective_license_expression,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].effective_license_name,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].imported_declared_license_expression,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].imported_declared_license_name,
                "GPL-2.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[24].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            )
            self.assertEqual(
                license_components[24].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                ),
            )

        # --- Third import with some changes ---

        license_policy = license_policy_standard
        license_policy.ignore_component_types = "npm"
        license_policy.save()

        license_policy_item = License_Policy_Item(
            license_policy=license_policy_standard,
            license_group=None,
            license=License.objects.get(spdx_id="0BSD"),
            non_spdx_license="",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        )
        license_policy_item.save()

        license_policy_item = License_Policy_Item(
            license_policy=license_policy_standard,
            license_group=None,
            license=None,
            non_spdx_license="attrs non-standard license",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        )
        license_policy_item.save()

        license_policy_item = License_Policy_Item(
            license_policy=license_policy_standard,
            license_group=None,
            license=License.objects.get(spdx_id="MIT"),
            non_spdx_license="",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        )
        license_policy_item.save()

        license_policy_item = License_Policy_Item(
            license_policy=license_policy_standard,
            license_group=None,
            license=License.objects.get(spdx_id="Apache-2.0"),
            non_spdx_license="",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        )
        license_policy_item.save()

        file_upload_parameters = FileUploadParameters(
            product=product,
            branch=branch,
            file=File(
                open(
                    "unittests/import_observations/parsers/cyclone_dx/files/changed/licenses_1.json",
                    "r",
                )
            ),
            service_name=service,
            docker_image_name_tag=docker_image_name_tag,
            endpoint_url=endpoint_url,
            kubernetes_cluster=kubernetes_cluster,
            kubernetes_namespace=kubernetes_namespace,
            kubernetes_resource_type=kubernetes_resource_type,
            kubernetes_resource_name=kubernetes_resource_name,
            suppress_licenses=suppress_licenses,
            sbom=sbom,
        )

        (
            new_observations,
            updated_observations,
            resolved_observations,
            new_license_objects,
            updated_license_objects,
            deleted_license_objects,
        ) = file_upload_observations(file_upload_parameters)

        settings = Settings.load()
        if settings.feature_license_management and not suppress_licenses:
            self.assertEqual(new_observations, 0)
            self.assertEqual(updated_observations, 0)
            self.assertEqual(resolved_observations, 0)
            self.assertEqual(new_license_objects, 3)
            self.assertEqual(updated_license_objects, 64)
            self.assertEqual(deleted_license_objects, 3)

            license_components = License_Component.objects.filter(product=1).order_by("id")
            self.assertEqual(len(license_components), 67)

            self.assertEqual(
                license_components[64].component_name_version,
                "argon2-cffi-bindings:21.2.1",
            )
            self.assertEqual(license_components[64].effective_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[64].effective_license_name, "MIT")
            self.assertEqual(license_components[64].imported_concluded_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[64].imported_concluded_license_name, "MIT")
            self.assertEqual(
                license_components[64].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            )
            self.assertEqual(
                license_components[64].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                ),
            )

            self.assertEqual(license_components[2].component_name_version, "asgiref:3.8.1")
            self.assertEqual(license_components[2].effective_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[2].effective_license_name, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[2].imported_concluded_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[2].imported_concluded_license_name, "0BSD, BSD-3-Clause")
            self.assertEqual(
                license_components[2].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            )
            self.assertEqual(
                license_components[2].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                ),
            )

            self.assertEqual(license_components[3].component_name_version, "attrs:24.2.0")
            self.assertEqual(license_components[3].effective_non_spdx_license, "attrs non-standard license")
            self.assertEqual(license_components[3].effective_license_name, "attrs non-standard license")
            self.assertEqual(license_components[3].imported_concluded_non_spdx_license, "attrs non-standard license")
            self.assertEqual(license_components[3].imported_concluded_license_name, "attrs non-standard license")
            self.assertEqual(
                license_components[3].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            )
            self.assertEqual(
                license_components[3].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                ),
            )

            self.assertEqual(license_components[7].component_name_version, "cryptography:43.0.1")
            self.assertEqual(
                license_components[7].effective_license_expression,
                "LGPL-3.0-or-later OR GPL-3.0-or-later",
            )
            self.assertEqual(
                license_components[7].effective_license_name,
                "LGPL-3.0-or-later OR GPL-3.0-or-later",
            )
            self.assertEqual(
                license_components[7].imported_concluded_license_expression,
                "LGPL-3.0-or-later OR GPL-3.0-or-later",
            )
            self.assertEqual(
                license_components[7].imported_concluded_license_name,
                "LGPL-3.0-or-later OR GPL-3.0-or-later",
            )
            self.assertEqual(
                license_components[7].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED,
            )
            self.assertEqual(
                license_components[7].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED,
                ),
            )

            self.assertEqual(license_components[8].component_name_version, "cvss:3.2")
            self.assertEqual(
                license_components[8].effective_license_expression,
                "LGPL-3.0-or-later AND BSD-3-Clause",
            )
            self.assertEqual(
                license_components[8].imported_concluded_license_expression,
                "LGPL-3.0-or-later AND BSD-3-Clause",
            )
            self.assertEqual(
                license_components[8].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED,
            )
            self.assertEqual(
                license_components[8].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED,
                ),
            )

            self.assertEqual(license_components[9].component_name_version, "defusedcsv:2.0.0")
            self.assertEqual(
                license_components[9].effective_license_expression,
                "Apache-2.0 AND (BSD-3-Clause OR MIT)",
            )
            self.assertEqual(
                license_components[9].imported_concluded_license_expression,
                "Apache-2.0 AND (BSD-3-Clause OR MIT)",
            )
            self.assertEqual(
                license_components[9].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            )
            self.assertEqual(
                license_components[9].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                ),
            )

            self.assertEqual(license_components[22].component_name_version, "email-validator:2.1.1")
            self.assertEqual(
                license_components[22].effective_license_expression,
                "GPL-3.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[22].imported_concluded_license_expression,
                "GPL-3.0-or-later WITH Bison-exception-2.2",
            )
            self.assertEqual(
                license_components[22].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            )
            self.assertEqual(
                license_components[22].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_UNKNOWN,
                ),
            )

        # --- Fourth import with ignoring the PiPy packages ---

        license_policy = license_policy_standard
        license_policy.ignore_component_types = "npm, pypi"
        license_policy.save()

        file_upload_parameters = FileUploadParameters(
            product=product,
            branch=branch,
            file=File(
                open(
                    "unittests/import_observations/parsers/cyclone_dx/files/changed/licenses_1.json",
                    "r",
                )
            ),
            service_name=service,
            docker_image_name_tag=docker_image_name_tag,
            endpoint_url=endpoint_url,
            kubernetes_cluster=kubernetes_cluster,
            kubernetes_namespace=kubernetes_namespace,
            kubernetes_resource_type=kubernetes_resource_type,
            kubernetes_resource_name=kubernetes_resource_name,
            suppress_licenses=suppress_licenses,
            sbom=sbom,
        )

        (
            new_observations,
            updated_observations,
            resolved_observations,
            new_license_objects,
            updated_license_objects,
            deleted_license_objects,
        ) = file_upload_observations(file_upload_parameters)

        settings = Settings.load()
        if settings.feature_license_management and not suppress_licenses:
            self.assertEqual(new_observations, 0)
            self.assertEqual(updated_observations, 0)
            self.assertEqual(resolved_observations, 0)
            self.assertEqual(new_license_objects, 0)
            self.assertEqual(updated_license_objects, 67)
            self.assertEqual(deleted_license_objects, 0)

            license_components = License_Component.objects.filter(product=1).order_by("id")
            self.assertEqual(len(license_components), 67)

            self.assertEqual(
                license_components[64].component_name_version,
                "argon2-cffi-bindings:21.2.1",
            )
            self.assertEqual(license_components[64].effective_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(license_components[64].imported_concluded_spdx_license, License.objects.get(spdx_id="MIT"))
            self.assertEqual(
                license_components[64].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_IGNORED,
            )
            self.assertEqual(
                license_components[64].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_IGNORED,
                ),
            )

            self.assertEqual(license_components[2].component_name_version, "asgiref:3.8.1")
            self.assertEqual(license_components[2].effective_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(license_components[2].imported_concluded_multiple_licenses, "0BSD, BSD-3-Clause")
            self.assertEqual(
                license_components[2].evaluation_result,
                License_Policy_Evaluation_Result.RESULT_IGNORED,
            )
            self.assertEqual(
                license_components[2].numerical_evaluation_result,
                License_Policy_Evaluation_Result.NUMERICAL_RESULTS.get(
                    License_Policy_Evaluation_Result.RESULT_IGNORED,
                ),
            )
        else:
            self.assertEqual(new_observations, 0)
            self.assertEqual(updated_observations, 0)
            self.assertEqual(resolved_observations, 0)
            self.assertEqual(new_license_objects, 0)
            self.assertEqual(updated_license_objects, 0)
            self.assertEqual(deleted_license_objects, 0)

            license_components = License_Component.objects.filter(product=1)
            self.assertEqual(len(license_components), 0)


class TestProcessLicenseComponentsServices(BaseTestCase):
    def setUp(self):
        call_command(
            "loaddata",
            ["unittests/fixtures/initial_license_data.json", "unittests/fixtures/unittests_fixtures.json"],
        )
        super().setUp()
        self.product = Product.objects.get(id=1)
        self.branch = Branch.objects.get(id=1)

    def _import(self, service, component_names):
        vulnerability_check, _ = Vulnerability_Check.objects.get_or_create(
            product=self.product, branch=self.branch, service=service, filename="sbom.json"
        )
        components = [License_Component(component_name=name, component_version="1.0") for name in component_names]
        return process_license_components(components, "scanner", vulnerability_check)

    def _component_names(self, service):
        return sorted(
            License_Component.objects.filter(
                product=self.product, origin_service=service, upload_filename="sbom.json"
            ).values_list("component_name", flat=True)
        )

    def test_same_filename_with_different_services(self):
        service_1 = Service.objects.get(id=1)
        service_2 = Service.objects.get(id=2)

        self.assertEqual(self._import(service_1, ["a", "b"]), (2, 0, 0))
        self.assertEqual(self._import(service_2, ["b", "c"]), (2, 0, 0))

        self.assertEqual(self._component_names(service_1), ["a", "b"])
        self.assertEqual(self._component_names(service_2), ["b", "c"])

        # A repeated import updates and deletes only the components of the same service
        self.assertEqual(self._import(service_1, ["b"]), (0, 1, 1))

        self.assertEqual(self._component_names(service_1), ["b"])
        self.assertEqual(self._component_names(service_2), ["b", "c"])

    def test_without_service_does_not_touch_components_of_services(self):
        service_1 = Service.objects.get(id=1)

        self.assertEqual(self._import(service_1, ["a"]), (1, 0, 0))
        self.assertEqual(self._import(None, ["b"]), (1, 0, 0))

        self.assertEqual(self._component_names(service_1), ["a"])
        self.assertEqual(self._component_names(None), ["b"])

    def test_license_policy_excludes_components_of_import(self):
        self.product.license_policy = License_Policy.objects.get(name="Standard")
        self.product.save()
        service_1 = Service.objects.get(id=1)

        self.assertEqual(self._import(service_1, ["a", "b"]), (2, 0, 0))
        self.assertEqual(self._import(None, ["c"]), (1, 0, 0))

        # Import without service: only the components with service are evaluated by the license policy
        self._set_outdated_evaluation_results()
        with patch(
            "application.licenses.services.license_policy.apply_license_policy_to_component",
            wraps=apply_license_policy_to_component,
        ) as mock_apply:
            self.assertEqual(self._import(None, ["c"]), (0, 1, 0))
        self.assertEqual(["a", "b"], self._evaluated_component_names(mock_apply))
        self._assert_evaluation_results_unknown()

        # Import with service: only the component without service is evaluated by the license policy
        self._set_outdated_evaluation_results()
        with patch(
            "application.licenses.services.license_policy.apply_license_policy_to_component",
            wraps=apply_license_policy_to_component,
        ) as mock_apply:
            self.assertEqual(self._import(service_1, ["a", "b"]), (0, 2, 0))
        self.assertEqual(["c"], self._evaluated_component_names(mock_apply))
        self._assert_evaluation_results_unknown()

    def test_license_policy_excludes_components_of_import_without_branch(self):
        self.product.license_policy = License_Policy.objects.get(name="Standard")
        self.product.save()
        # Without a branch, all license components of the product are evaluated, including ones
        # committed by other test classes
        License_Component.objects.filter(product=self.product).delete()

        self.assertEqual(self._import(None, ["a"]), (1, 0, 0))
        self.assertEqual(self._import_without_branch(["b"]), (1, 0, 0))

        License_Component.objects.filter(product=self.product).update(
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED
        )

        # Without a branch, the license policy is applied to all branches of the product. The component
        # with the same service and file name in another branch is not part of this import and must be evaluated.
        with patch(
            "application.licenses.services.license_policy.apply_license_policy_to_component",
            wraps=apply_license_policy_to_component,
        ) as mock_apply:
            self.assertEqual(self._import_without_branch(["b"]), (0, 1, 0))
        self.assertEqual(["a"], self._evaluated_component_names(mock_apply))
        self.assertEqual(
            {License_Policy_Evaluation_Result.RESULT_UNKNOWN},
            set(License_Component.objects.filter(product=self.product).values_list("evaluation_result", flat=True)),
        )

    def _import_without_branch(self, component_names):
        vulnerability_check, _ = Vulnerability_Check.objects.get_or_create(
            product=self.product, branch=None, service=None, filename="sbom.json"
        )
        components = [License_Component(component_name=name, component_version="1.0") for name in component_names]
        return process_license_components(components, "scanner", vulnerability_check)

    def _set_outdated_evaluation_results(self):
        # The components have no license, so the license policy evaluates them as unknown.
        # Only the branch is relevant, because the license policy is applied to the components of the branch.
        License_Component.objects.filter(product=self.product, branch=self.branch).update(
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED
        )

    def _evaluated_component_names(self, mock_apply):
        return sorted(mock_call.args[0].component_name for mock_call in mock_apply.call_args_list)

    def _assert_evaluation_results_unknown(self):
        self.assertEqual(
            {License_Policy_Evaluation_Result.RESULT_UNKNOWN},
            set(
                License_Component.objects.filter(product=self.product, branch=self.branch).values_list(
                    "evaluation_result", flat=True
                )
            ),
        )

    def test_url_and_copyright(self):
        vulnerability_check, _ = Vulnerability_Check.objects.get_or_create(
            product=self.product, branch=self.branch, service=None, filename="sbom.json"
        )

        def import_component(url, copyright_text):
            component = License_Component(
                component_name="a", component_version="1.0", component_url=url, component_copyright=copyright_text
            )
            return process_license_components([component], "scanner", vulnerability_check)

        self.assertEqual(import_component("https://a.example.com", "Copyright (c) A"), (1, 0, 0))
        license_component = License_Component.objects.get(product=self.product, upload_filename="sbom.json")
        self.assertEqual(license_component.component_url, "https://a.example.com")
        self.assertEqual(license_component.component_copyright, "Copyright (c) A")

        # A repeated import updates both fields of the existing component
        self.assertEqual(import_component("https://b.example.com", "Copyright (c) B"), (0, 1, 0))
        license_component.refresh_from_db()
        self.assertEqual(license_component.component_url, "https://b.example.com")
        self.assertEqual(license_component.component_copyright, "Copyright (c) B")

        self.assertEqual(import_component(None, None), (0, 1, 0))
        license_component.refresh_from_db()
        self.assertEqual(license_component.component_url, "")
        self.assertEqual(license_component.component_copyright, "")

    def _import_with_purl(self, purl):
        vulnerability_check, _ = Vulnerability_Check.objects.get_or_create(
            product=self.product, branch=self.branch, service=None, filename="sbom.json"
        )
        component = License_Component(component_name="django", component_version="6.0.7", component_purl=purl)
        return process_license_components([component], "scanner", vulnerability_check)

    def _license_component(self):
        return License_Component.objects.select_related("component").get(
            product=self.product, upload_filename="sbom.json"
        )

    def test_core_component_changed_purl(self):
        self.assertEqual(self._import_with_purl(None), (1, 0, 0))
        license_component = self._license_component()
        self.assertEqual("", license_component.component.purl)
        self.assertEqual("django:6.0.7", license_component.component.name_version)

        # Same license component, but the purl leads to a different core component
        self.assertEqual(self._import_with_purl("pkg:pypi/django@6.0.7"), (0, 1, 0))
        license_component = self._license_component()
        self.assertEqual("pkg:pypi/django@6.0.7", license_component.component_purl)
        self.assertEqual("pkg:pypi/django@6.0.7", license_component.component.purl)

        self.assertEqual(self._import_with_purl("pkg:pypi/django@6.0.7?arch=amd64"), (0, 1, 0))
        license_component_qualifiers = self._license_component()
        # Qualifiers are not part of the identity of the core component
        self.assertEqual(license_component.component_id, license_component_qualifiers.component_id)

    def test_core_component_unchanged_purl(self):
        self.assertEqual(self._import_with_purl("pkg:pypi/django@6.0.7"), (1, 0, 0))
        component_id = self._license_component().component_id

        with CaptureQueriesContext(connection) as context:
            self.assertEqual(self._import_with_purl("pkg:pypi/django@6.0.7"), (0, 1, 0))

        self.assertEqual(component_id, self._license_component().component_id)
        # The license component queries join the core components, only direct accesses are relevant here
        core_component_queries = [
            query["sql"]
            for query in context.captured_queries
            if query["sql"].startswith('SELECT "core_component"')
            or query["sql"].startswith('INSERT INTO "core_component"')
        ]
        self.assertEqual([], core_component_queries)

    def test_core_component_missing(self):
        self.assertEqual(self._import_with_purl("pkg:pypi/django@6.0.7"), (1, 0, 0))
        License_Component.objects.filter(product=self.product, upload_filename="sbom.json").update(component=None)

        self.assertEqual(self._import_with_purl("pkg:pypi/django@6.0.7"), (0, 1, 0))
        self.assertEqual("pkg:pypi/django@6.0.7", self._license_component().component.purl)


class APIImportObservation(BaseTestCase):
    def setUp(self):
        Observation.objects.all().delete()
        Observation_Log.objects.all().delete()
        Rule.objects.all().delete()
        Vulnerability_Check.objects.all().delete()
        call_command("loaddata", "unittests/fixtures/import_observations_fixtures.json")
        super().setUp()

    @patch("application.import_observations.parsers.dependency_track.parser.DependencyTrack.check_connection")
    def test_api_import_no_connection(self, mock_check_connection):
        mock_check_connection.return_value = False, ["error_1", "error_2"], {}

        api_configuration = Api_Configuration(product=self.product_1, parser=Parser.objects.get(id=3))
        parameters = ApiImportParameters(
            api_configuration=api_configuration,
            branch=None,
            service_name="",
            docker_image_name_tag="",
            endpoint_url="",
            kubernetes_cluster="",
            kubernetes_namespace="",
            kubernetes_resource_type="",
            kubernetes_resource_name="",
        )

        with self.assertRaises(ValidationError) as e:
            api_import_observations(parameters)

        self.assertEqual(
            "[ErrorDetail(string=\"Connection couldn't be established: error_1 / error_2\", code='invalid')]",
            str(e.exception),
        )
        mock_check_connection.assert_called_with(api_configuration)

    @patch("application.import_observations.parsers.dependency_track.parser.DependencyTrack.check_connection")
    @patch("application.import_observations.parsers.dependency_track.parser.DependencyTrack.get_observations")
    @patch("application.import_observations.services.import_observations._process_data")
    @patch("application.import_observations.models.Vulnerability_Check.objects.update_or_create")
    def test_api_import_success(
        self, mock_update_or_create, mock_process_data, mock_get_observations, mock_check_connection
    ):
        mock_check_connection.return_value = True, [], {"data": "data"}
        mock_get_observations.return_value = [self.observation_1], "test_scanner"
        mock_process_data.return_value = 1, 2, 3

        api_configuration = Api_Configuration(
            name="test_configuration", product=self.product_1, parser=Parser.objects.get(id=3)
        )
        parameters = ApiImportParameters(
            api_configuration=api_configuration,
            branch=self.branch_1,
            service_name=None,
            docker_image_name_tag="",
            endpoint_url="",
            kubernetes_cluster="",
            kubernetes_namespace="",
            kubernetes_resource_type="",
            kubernetes_resource_name="",
        )

        numbers = api_import_observations(parameters)

        self.assertEqual(1, numbers[0])
        self.assertEqual(2, numbers[1])
        self.assertEqual(3, numbers[2])

        mock_check_connection.assert_called_with(api_configuration)
        mock_get_observations.assert_called_with({"data": "data"}, self.product_1, self.branch_1)
        mock_update_or_create.assert_called_with(
            product=self.product_1,
            branch=self.branch_1,
            service=None,
            filename="",
            api_configuration_name="test_configuration",
            defaults={
                "last_import_observations_new": 1,
                "last_import_observations_updated": 2,
                "last_import_observations_resolved": 3,
                "scanner": "test_scanner",
            },
        )


class TestDeduplicateCrossScanner(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        # Create an observation with all origin fields set
        self.observation = Observation(
            product=self.product_1,
            title="test_observation",
            branch=self.branch_1,
            scanner="scanner_1",
            origin_service=self.service_1,
            origin_component_name_version="component_1",
            origin_docker_image_name_tag="docker_1",
            origin_endpoint_url="https://example.com",
            origin_source_file="/path/to/file",
            origin_source_line_start=1,
            origin_source_line_end=10,
            origin_cloud_qualified_resource="cloud_resource",
            origin_kubernetes_qualified_resource="k8s_resource",
        )

    @patch("application.import_observations.services.import_observations.logger")
    def test_deduplicate_cross_scanner_disabled(self, mock_logger):
        """Test when feature is disabled, returns False without checking DB."""
        settings = type("Settings", (), {"feature_cross_scanner_deduplication": False})()
        result = _deduplicate_cross_scanner(self.observation, settings)

        self.assertFalse(result)
        mock_logger.info.assert_not_called()

    @patch("application.import_observations.services.import_observations.logger")
    @patch.object(Observation.objects, "filter")
    def test_deduplicate_cross_scanner_enabled_with_duplicate(self, mock_filter, mock_logger):
        """Test when feature is enabled and a duplicate exists."""
        # Mock the filter chain
        mock_filter_instance = mock_filter.return_value
        mock_filter_instance.exclude.return_value.exists.return_value = True

        settings = type("Settings", (), {"feature_cross_scanner_deduplication": True})()
        result = _deduplicate_cross_scanner(self.observation, settings)

        self.assertTrue(result)
        mock_filter.assert_called_once_with(
            product=self.observation.product,
            title=self.observation.title,
            branch=self.observation.branch,
            origin_service=self.observation.origin_service,
            origin_component_name_version=self.observation.origin_component_name_version,
            origin_docker_image_name_tag=self.observation.origin_docker_image_name_tag,
            origin_endpoint_url=self.observation.origin_endpoint_url,
            origin_source_file=self.observation.origin_source_file,
            origin_source_line_start=self.observation.origin_source_line_start,
            origin_source_line_end=self.observation.origin_source_line_end,
            origin_cloud_qualified_resource=self.observation.origin_cloud_qualified_resource,
            origin_kubernetes_qualified_resource=self.observation.origin_kubernetes_qualified_resource,
        )
        mock_filter_instance.exclude.assert_called_once_with(scanner=self.observation.scanner)
        mock_logger.info.assert_called_once()
        self.assertIn("test_observation", mock_logger.info.call_args[0][1])

    @patch.object(Observation.objects, "filter")
    def test_deduplicate_cross_scanner_enabled_no_duplicate(self, mock_filter):
        """Test when feature is enabled and no duplicate exists."""
        # Mock the filter chain
        mock_filter_instance = mock_filter.return_value
        mock_filter_instance.exclude.return_value.exists.return_value = False

        settings = type("Settings", (), {"feature_cross_scanner_deduplication": True})()
        result = _deduplicate_cross_scanner(self.observation, settings)

        self.assertFalse(result)
        mock_filter.assert_called_once()
        mock_filter_instance.exclude.assert_called_once()


class TestProcessCurrentObservation(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.apply_epss")
    def test_component_url_updated(self, mock_apply_epss, mock_apply_exploit_information):
        imported_observation = Observation.objects.get(id=1)
        imported_observation.origin_component_url = "https://new.example.com"
        observation_before = Observation.objects.get(id=1)
        settings = Settings.load()

        _process_current_observation(imported_observation, observation_before, settings, {}, {})

        self.assertEqual("https://new.example.com", Observation.objects.get(id=1).origin_component_url)
        mock_apply_epss.assert_called_once_with(observation_before, {})
        mock_apply_exploit_information.assert_called_once_with(observation_before, settings, {})

    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.apply_epss")
    def test_severity_changed_saves_only_changed_fields(self, mock_apply_epss, mock_apply_exploit_information):
        imported_observation = Observation.objects.get(id=1)
        imported_observation.parser_severity = Severity.SEVERITY_CRITICAL
        observation_before = Observation.objects.get(id=1)
        # Concurrent change after the observation has been loaded must not be overwritten
        Observation.objects.filter(id=1).update(recommendation="concurrent change")

        _process_current_observation(imported_observation, observation_before, Settings.load(), {}, {})

        observation = Observation.objects.get(id=1)
        self.assertEqual("concurrent change", observation.recommendation)
        self.assertEqual(Severity.SEVERITY_CRITICAL, observation.current_severity)

    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.apply_epss")
    def test_origin_fields_updated(self, mock_apply_epss, mock_apply_exploit_information):
        observation = self._process_imported_observation(
            origin_component_cpe="cpe:2.3:a:new:new:1.0:*:*:*:*:*:*:*",
            origin_docker_image_digest="sha256:new",
            origin_cloud_resource_type="new_resource_type",
        )

        self.assertEqual("cpe:2.3:a:new:new:1.0:*:*:*:*:*:*:*", observation.origin_component_cpe)
        self.assertEqual("sha256:new", observation.origin_docker_image_digest)
        self.assertEqual("new_resource_type", observation.origin_cloud_resource_type)

    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.apply_epss")
    def test_docker_image_tag_removed(self, mock_apply_epss, mock_apply_exploit_information):
        observation = Observation.objects.get(id=1)
        observation.origin_docker_image_name_tag = "registry.example.com/app:1.0"
        observation.save()
        self.assertEqual("1.0", observation.origin_docker_image_tag)

        observation = self._process_imported_observation(
            origin_docker_image_name="registry.example.com/app",
            origin_docker_image_tag="",
            origin_docker_image_name_tag="",
        )

        self.assertEqual("registry.example.com/app", observation.origin_docker_image_name)
        self.assertEqual("", observation.origin_docker_image_tag)
        self.assertEqual("registry.example.com/app", observation.origin_docker_image_name_tag)
        self.assertEqual("app", observation.origin_docker_image_name_tag_short)

    @patch("application.import_observations.services.import_observations.apply_exploit_information")
    @patch("application.import_observations.services.import_observations.apply_epss")
    def test_component_purl_updated(self, mock_apply_epss, mock_apply_exploit_information):
        observation = Observation.objects.get(id=1)
        observation.origin_component = None
        observation.origin_component_name_version = "openssl:3.0.11"
        observation.save()
        component_without_purl = observation.origin_component
        self.assertEqual("", component_without_purl.purl)

        # The component belongs to the purl
        purl = "pkg:deb/debian/openssl@3.0.11"
        observation = self._process_imported_purl(f"{purl}?distro=debian-12.5")
        self.assertEqual(f"{purl}?distro=debian-12.5", observation.origin_component_purl)
        self.assertEqual("deb", observation.origin_component_purl_type)
        self.assertEqual(purl, observation.origin_component.purl)
        component_with_purl = observation.origin_component

        # The qualifiers of the purl are not part of the component
        observation = self._process_imported_purl(f"{purl}?distro=debian-12.6")
        self.assertEqual(f"{purl}?distro=debian-12.6", observation.origin_component_purl)
        self.assertEqual(component_with_purl, observation.origin_component)

        observation = self._process_imported_purl("")
        self.assertEqual("", observation.origin_component_purl)
        self.assertEqual("", observation.origin_component_purl_type)
        self.assertEqual(component_without_purl, observation.origin_component)

    def _process_imported_purl(self, purl):
        # The parsers set neither the component nor the type of the purl
        return self._process_imported_observation(
            origin_component=None, origin_component_purl=purl, origin_component_purl_type=""
        )

    def _process_imported_observation(self, **fields):
        imported_observation = Observation.objects.get(id=1)
        for name, value in fields.items():
            setattr(imported_observation, name, value)
        normalize_observation_fields(imported_observation)

        _process_current_observation(imported_observation, Observation.objects.get(id=1), Settings.load(), {}, {})

        return Observation.objects.get(id=1)

    def test_cvss_bt_vector_set_with_log(self):
        observation_logs = self._process_cvss_bt(stored_cvss3_vector="")

        self.assertEqual(1, len(observation_logs))
        self.assertEqual(
            f"{Observation_Log_Comment.COMMENT_PREFIX_CVSS_VECTOR_SET_BY_CVSS_BT}{CVSS_BT_VECTOR}",
            observation_logs[0].comment,
        )
        self.assertEqual("", observation_logs[0].severity)
        self.assertEqual(Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED, observation_logs[0].assessment_status)
        observation = Observation.objects.get(id=1)
        self.assertEqual(CVSS_BT_VECTOR, observation.cvss3_vector)
        self.assertEqual(observation_logs[0].created, observation.last_observation_log)

    def test_cvss_bt_vector_already_stored_without_log(self):
        observation_logs = self._process_cvss_bt(stored_cvss3_vector=CVSS_BT_VECTOR)

        self.assertEqual(0, len(observation_logs))
        self.assertEqual(CVSS_BT_VECTOR, Observation.objects.get(id=1).cvss3_vector)

    def test_new_observation_cvss_bt_vector_set_with_log(self):
        observation_logs = self._process_new_cvss_bt(Severity.SEVERITY_UNKNOWN)

        self.assertEqual(
            [
                (Observation_Log_Comment.COMMENT_SET_BY_PARSER, Severity.SEVERITY_UNKNOWN),
                (
                    f"{Observation_Log_Comment.COMMENT_PREFIX_CVSS_VECTOR_SET_BY_CVSS_BT}{CVSS_BT_VECTOR}",
                    Severity.SEVERITY_HIGH,
                ),
            ],
            observation_logs,
        )

    def test_new_observation_cvss_bt_severity_unchanged(self):
        observation_logs = self._process_new_cvss_bt(Severity.SEVERITY_MEDIUM)

        self.assertEqual(
            [
                (Observation_Log_Comment.COMMENT_SET_BY_PARSER, Severity.SEVERITY_MEDIUM),
                (f"{Observation_Log_Comment.COMMENT_PREFIX_CVSS_VECTOR_SET_BY_CVSS_BT}{CVSS_BT_VECTOR}", ""),
            ],
            observation_logs,
        )

    def _process_new_cvss_bt(self, parser_severity):
        imported_observation = Observation(
            title="cvss-bt",
            vulnerability_id="CVE-2025-0001",
            parser_severity=parser_severity,
            product_id=1,
            parser_id=1,
            import_last_seen=timezone.now(),
        )

        _process_new_observation(
            imported_observation, self._cvss_bt_settings(), {}, self._cvss_bt_exploit_informations()
        )

        return list(
            Observation_Log.objects.filter(observation=imported_observation)
            .order_by("id")
            .values_list("comment", "severity")
        )

    def _process_cvss_bt(self, stored_cvss3_vector):
        Observation.objects.filter(id=1).update(vulnerability_id="CVE-2025-0001", cvss3_vector=stored_cvss3_vector)
        imported_observation = Observation.objects.get(id=1)
        # The parser delivers no vector
        imported_observation.cvss3_vector = ""

        _process_current_observation(
            imported_observation,
            Observation.objects.get(id=1),
            self._cvss_bt_settings(),
            {},
            self._cvss_bt_exploit_informations(),
        )

        return list(
            Observation_Log.objects.filter(
                observation_id=1, comment__startswith=Observation_Log_Comment.COMMENT_PREFIX_CVSS_VECTOR_SET_BY_CVSS_BT
            )
        )

    def _cvss_bt_settings(self):
        settings = Settings.load()
        settings.feature_exploit_information = True
        return settings

    def _cvss_bt_exploit_informations(self):
        return {"CVE-2025-0001": Exploit_Information(cve="CVE-2025-0001", base_cvss_vector=CVSS_BT_VECTOR)}


class TestResolveUnimportedObservations(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def test_resolved_saves_only_changed_fields(self):
        Observation.objects.filter(id=1).update(
            parser_status=Status.STATUS_OPEN, assessment_status="", current_status=Status.STATUS_OPEN
        )
        observation = Observation.objects.get(id=1)
        # Concurrent change after the observation has been loaded must not be overwritten
        Observation.objects.filter(id=1).update(recommendation="concurrent change")

        _resolve_unimported_observations({"hash": observation})

        observation = Observation.objects.get(id=1)
        self.assertEqual("concurrent change", observation.recommendation)
        self.assertEqual(Status.STATUS_RESOLVED, observation.parser_status)
        self.assertEqual(Status.STATUS_RESOLVED, observation.current_status)

    @patch("application.core.models.Observation.save")
    @patch("application.import_observations.services.import_observations.create_observation_log")
    def test_already_resolved(self, mock_create_observation_log, mock_save):
        observation = Observation(pk=1, parser_status=Status.STATUS_RESOLVED, current_status=Status.STATUS_RESOLVED)

        self.assertEqual(set(), _resolve_unimported_observations({"hash": observation}))

        mock_save.assert_not_called()
        mock_create_observation_log.assert_not_called()

    @patch("application.core.models.Observation.save")
    @patch("application.import_observations.services.import_observations.create_observation_log")
    def test_resolved_with_log(self, mock_create_observation_log, mock_save):
        observation = Observation(pk=1, parser_status=Status.STATUS_OPEN, current_status=Status.STATUS_OPEN)

        self.assertEqual({observation}, _resolve_unimported_observations({"hash": observation}))

        self.assertEqual(Status.STATUS_RESOLVED, observation.current_status)
        mock_create_observation_log.assert_called_once()
        self.assertEqual(Status.STATUS_RESOLVED, mock_create_observation_log.call_args.kwargs["status"])
        # create_observation_log saves the observation
        mock_save.assert_not_called()

    @patch("application.core.models.Observation.save")
    @patch("application.import_observations.services.import_observations.create_observation_log")
    def test_resolved_by_assessment_without_log(self, mock_create_observation_log, mock_save):
        observation = Observation(
            pk=1,
            parser_status=Status.STATUS_OPEN,
            assessment_status=Status.STATUS_RESOLVED,
            current_status=Status.STATUS_RESOLVED,
        )

        self.assertEqual(set(), _resolve_unimported_observations({"hash": observation}))

        self.assertEqual(Status.STATUS_RESOLVED, observation.parser_status)
        mock_save.assert_called_once()
        mock_create_observation_log.assert_not_called()


class RequestMock:
    def __init__(self, user):
        self.user = user
