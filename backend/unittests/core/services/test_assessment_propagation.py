from datetime import timedelta
from typing import Optional
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from application.access_control.models import User
from application.core.models import Branch, Observation, Observation_Log, Product
from application.core.services.assessment import (
    _get_compiled_branches,
    _get_product_group_propagate_branches,
    _get_product_propagate_branches,
    propagate_assessment,
    set_propagated_assessment_for_new_observation,
)
from application.core.types import Assessment_Status, Severity, Status
from application.rules.models import Rule
from application.vex.models import VEX_Document, VEX_Statement
from application.vex.types import VEX_Document_Type, VEX_Status
from unittests.base_test_case import BaseTestCase


class TestGetProductPropagateBranches(BaseTestCase):
    def test_no_configuration(self) -> None:
        self.assertEqual([], _get_product_propagate_branches(self.observation_1))

    def test_configuration(self) -> None:
        self.product_1.propagate_branches = [{"propagate_to": "release-.*"}]
        self.assertEqual([{"propagate_to": "release-.*"}], _get_product_propagate_branches(self.observation_1))


class TestGetProductGroupPropagateBranches(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.product_1.product_group = self.product_group_1

    def test_no_product_group(self) -> None:
        self.product_1.product_group = None
        self.product_group_1.propagate_branches = [{"propagate_to": "main"}]
        self.assertEqual([], _get_product_group_propagate_branches(self.observation_1))

    def test_no_configuration(self) -> None:
        self.assertEqual([], _get_product_group_propagate_branches(self.observation_1))

    def test_configuration(self) -> None:
        self.product_group_1.propagate_branches = [{"propagate_to": "main"}]
        self.assertEqual([{"propagate_to": "main"}], _get_product_group_propagate_branches(self.observation_1))


class TestGetCompiledBranches(BaseTestCase):
    def test_matching_pattern(self) -> None:
        compiled_branches = _get_compiled_branches(self.observation_1, [{"propagate_to": "branch_.*"}])
        self.assertEqual({"branch_.*"}, {pattern.pattern for pattern in compiled_branches})

    def test_non_matching_pattern(self) -> None:
        compiled_branches = _get_compiled_branches(self.observation_1, [{"propagate_to": "release-.*"}])
        self.assertEqual(set(), compiled_branches)

    def test_only_matching_patterns_are_compiled(self) -> None:
        compiled_branches = _get_compiled_branches(
            self.observation_1,
            [{"propagate_to": "branch_.*"}, {"propagate_to": "release-.*"}, {"propagate_to": "branch_1"}],
        )
        self.assertEqual({"branch_.*", "branch_1"}, {pattern.pattern for pattern in compiled_branches})

    def test_pattern_is_anchored_at_the_beginning(self) -> None:
        compiled_branches = _get_compiled_branches(self.observation_1, [{"propagate_to": "ranch_.*"}])
        self.assertEqual(set(), compiled_branches)


class BasePropagationTestCase(TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        # remove fixture observation logs, they must not interfere with the candidate selection
        Observation_Log.objects.all().delete()

        self.product = Product.objects.get(pk=1)
        self.product.propagate_branches = [{"propagate_to": "db_branch_internal_.*"}]
        self.product.save()

        self.branch_dev = Branch.objects.get(pk=1)
        self.branch_main = Branch.objects.get(pk=2)
        self.user = User.objects.get(pk=2)
        self.observation_dev = Observation.objects.get(pk=1)
        self.observation_dev.origin_component_name_version = "component_name:version"
        self.observation_dev.save()
        # re-fetch so the cached product relation (populated by the pre_save signal) does not
        # shadow propagate_branches changes made by individual tests
        self.observation_dev = Observation.objects.get(pk=1)

    def _create_branch(self, name: str) -> Branch:
        return Branch.objects.create(product=self.product, name=name)

    def _configure_product_group_propagation_only(
        self, *, new_assessment: bool = True, new_observation: bool = True
    ) -> Product:
        # drive propagation exclusively via the product group by moving the branch
        # configuration to the group and clearing it on the product
        product_group = self.product.product_group
        product_group.propagate_branches = [{"propagate_to": "db_branch_internal_.*"}]
        product_group.propagate_branches_new_assessment = new_assessment
        product_group.propagate_branches_new_observation = new_observation
        product_group.save()
        self.product.propagate_branches = None
        self.product.save()
        return product_group

    def _clone_observation(
        self,
        branch: Optional[Branch],
        title: Optional[str] = None,
        origin_component_name_version: Optional[str] = None,
    ) -> Observation:
        observation = Observation.objects.get(pk=1)
        observation.pk = None
        observation.branch = branch
        if title is not None:
            observation.title = title
        if origin_component_name_version is not None:
            observation.origin_component_name_version = origin_component_name_version
        observation.save()
        return observation

    def _create_log(  # pylint: disable=too-many-arguments
        self,
        observation: Observation,
        *,
        severity: str = "",
        status: str = Status.STATUS_FALSE_POSITIVE,
        comment: str = "manual assessment",
        assessment_status: str = Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        propagated_from: Optional[Observation_Log] = None,
        general_rule: Optional[Rule] = None,
        product_rule: Optional[Rule] = None,
        vex_statement: Optional[VEX_Statement] = None,
        created=None,
    ) -> Observation_Log:
        observation_log = Observation_Log.objects.create(
            observation=observation,
            user=self.user,
            severity=severity,
            status=status,
            priority=None,
            comment=comment,
            vex_justification="",
            vex_remediations=None,
            assessment_status=assessment_status,
            risk_acceptance_expiry_date=None,
            propagated_from=propagated_from,
            general_rule=general_rule,
            product_rule=product_rule,
            vex_statement=vex_statement,
        )
        if created:
            # created is set by auto_now_add, it can only be changed with an update
            Observation_Log.objects.filter(pk=observation_log.pk).update(created=created)
            observation_log.refresh_from_db()
        return observation_log


class TestPropagateAssessment(BasePropagationTestCase):
    @patch("application.core.services.assessment.save_assessment")
    def test_propagates_to_matching_branch(self, save_assessment_mock) -> None:
        target_observation = self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)

        propagate_assessment(source_log)

        save_assessment_mock.assert_called_once_with(
            observation=target_observation,
            new_severity=Severity.SEVERITY_HIGH,
            new_status=Status.STATUS_FALSE_POSITIVE,
            new_priority=None,
            comment="manual assessment",
            new_vex_justification="",
            new_vex_remediations=None,
            new_risk_acceptance_expiry_date=None,
            propagated_from=source_log,
        )

    @patch("application.core.services.assessment.save_assessment")
    def test_not_propagate_branches_new_assessment(self, save_assessment_mock) -> None:
        target_observation = self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)
        source_log.observation.product.propagate_branches_new_assessment = False

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_propagate_branches_new_assessment_product_group(self, save_assessment_mock) -> None:
        self._configure_product_group_propagation_only(new_assessment=True)
        self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)

        propagate_assessment(source_log)

        save_assessment_mock.assert_called_once()

    @patch("application.core.services.assessment.save_assessment")
    def test_not_propagate_branches_new_assessment_product_group(self, save_assessment_mock) -> None:
        self._configure_product_group_propagation_only(new_assessment=False)
        self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_observation_without_branch(self, save_assessment_mock) -> None:
        observation_without_branch = self._clone_observation(None, "Title", "component_name:version")
        self._clone_observation(self.branch_main)
        source_log = self._create_log(observation_without_branch)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_observation_without_origin_component_name_version(self, save_assessment_mock) -> None:
        observation_without_component = self._clone_observation(self.branch_dev, "Title", "")
        self._clone_observation(self.branch_main)
        source_log = self._create_log(observation_without_component)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_no_propagate_branches_configured(self, save_assessment_mock) -> None:
        self.product.propagate_branches = None
        self.product.save()
        self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_source_branch_not_matching(self, save_assessment_mock) -> None:
        self.product.propagate_branches = [{"propagate_to": "db_branch_internal_main"}]
        self.product.save()
        self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_target_branch_not_matching(self, save_assessment_mock) -> None:
        self.product.propagate_branches = [{"propagate_to": "db_branch_internal_dev.*"}]
        self.product.save()
        matching_branch = self._create_branch("db_branch_internal_dev_2")
        matching_observation = self._clone_observation(matching_branch)
        self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_called_once()
        self.assertEqual(matching_observation, save_assessment_mock.call_args.kwargs["observation"])

    @patch("application.core.services.assessment.save_assessment")
    def test_different_title_not_propagated(self, save_assessment_mock) -> None:
        self._clone_observation(self.branch_main, title="other_title")
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_different_origin_component_not_propagated(self, save_assessment_mock) -> None:
        self._clone_observation(self.branch_main, origin_component_name_version="other_component:1.0")
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()


class TestSetPropagatedAssessmentForNewObservation(BasePropagationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.new_branch = self._create_branch("db_branch_internal_new")
        self.new_observation = self._clone_observation(self.new_branch)
        self.observation_main = self._clone_observation(self.branch_main)

    @patch("application.core.services.assessment.save_assessment")
    def test_applies_newest_matching_assessment(self, save_assessment_mock) -> None:
        candidate_log = self._create_log(self.observation_main, severity=Severity.SEVERITY_HIGH)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_called_once_with(
            observation=self.new_observation,
            new_severity=Severity.SEVERITY_HIGH,
            new_status=Status.STATUS_FALSE_POSITIVE,
            new_priority=None,
            comment="manual assessment",
            new_vex_justification="",
            new_vex_remediations=None,
            new_risk_acceptance_expiry_date=None,
            propagated_from=candidate_log,
        )

    @patch("application.core.services.assessment.save_assessment")
    def test_not_propagate_branches_new_observation(self, save_assessment_mock) -> None:
        candidate_log = self._create_log(self.observation_main, severity=Severity.SEVERITY_HIGH)
        self.new_observation.product.propagate_branches_new_observation = False

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_propagate_branches_new_observation_product_group(self, save_assessment_mock) -> None:
        self._configure_product_group_propagation_only(new_observation=True)
        self._create_log(self.observation_main, severity=Severity.SEVERITY_HIGH)

        set_propagated_assessment_for_new_observation(Observation.objects.get(pk=self.new_observation.pk))

        save_assessment_mock.assert_called_once()

    @patch("application.core.services.assessment.save_assessment")
    def test_not_propagate_branches_new_observation_product_group(self, save_assessment_mock) -> None:
        self._configure_product_group_propagation_only(new_observation=False)
        self._create_log(self.observation_main, severity=Severity.SEVERITY_HIGH)

        set_propagated_assessment_for_new_observation(Observation.objects.get(pk=self.new_observation.pk))

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_newest_log_across_branches_wins(self, save_assessment_mock) -> None:
        other_branch = self._create_branch("db_branch_internal_release")
        observation_release = self._clone_observation(other_branch)
        self._create_log(self.observation_main, created=timezone.now() - timedelta(hours=2))
        newer_log = self._create_log(observation_release, created=timezone.now() - timedelta(hours=1))

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_called_once()
        self.assertEqual(newer_log, save_assessment_mock.call_args.kwargs["propagated_from"])

    @patch("application.core.services.assessment.save_assessment")
    def test_newest_log_within_branch_wins(self, save_assessment_mock) -> None:
        self._create_log(
            self.observation_main, status=Status.STATUS_IN_REVIEW, created=timezone.now() - timedelta(hours=2)
        )
        newer_log = self._create_log(self.observation_main, created=timezone.now() - timedelta(hours=1))

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_called_once()
        self.assertEqual(newer_log, save_assessment_mock.call_args.kwargs["propagated_from"])

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_propagated_logs(self, save_assessment_mock) -> None:
        # the referenced source log is itself excluded because it changes neither severity nor status
        source_log = self._create_log(self.observation_dev, severity="", status="")
        self._create_log(self.observation_main, propagated_from=source_log)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_from_general_rules(self, save_assessment_mock) -> None:
        general_rule = Rule.objects.create(name="general_rule")
        self._create_log(self.observation_main, general_rule=general_rule)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_from_product_rules(self, save_assessment_mock) -> None:
        product_rule = Rule.objects.create(name="product_rule", product=self.product)
        self._create_log(self.observation_main, product_rule=product_rule)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_from_vex_statements(self, save_assessment_mock) -> None:
        vex_document = VEX_Document.objects.create(
            type=VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF,
            document_id="document_id",
            version="1",
            current_release_date=timezone.now(),
            initial_release_date=timezone.now(),
            author="author",
        )
        vex_statement = VEX_Statement.objects.create(
            document=vex_document,
            vulnerability_id="CVE-2026-12345",
            status=VEX_Status.VEX_STATUS_NOT_AFFECTED,
        )
        self._create_log(self.observation_main, vex_statement=vex_statement)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_without_severity_and_status_change(self, save_assessment_mock) -> None:
        self._create_log(self.observation_main, severity="", status="")

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_set_by_parser(self, save_assessment_mock) -> None:
        self._create_log(self.observation_main, comment="Set by parser")

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_unapproved_logs(self, save_assessment_mock) -> None:
        for assessment_status in (
            Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
            Assessment_Status.ASSESSMENT_STATUS_REJECTED,
        ):
            with self.subTest(assessment_status=assessment_status):
                observation_log = self._create_log(self.observation_main, assessment_status=assessment_status)

                set_propagated_assessment_for_new_observation(self.new_observation)

                save_assessment_mock.assert_not_called()
                observation_log.delete()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_from_own_branch(self, save_assessment_mock) -> None:
        observation_same_branch = self._clone_observation(self.new_branch)
        self._create_log(observation_same_branch)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_from_not_matching_branch(self, save_assessment_mock) -> None:
        not_matching_branch = self._create_branch("feature_x")
        observation_feature = self._clone_observation(not_matching_branch)
        self._create_log(observation_feature)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_observation_without_branch(self, save_assessment_mock) -> None:
        observation_without_branch = self._clone_observation(None, "Title", "component_name:version")
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(observation_without_branch)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_observation_without_origin_component_name_version(self, save_assessment_mock) -> None:
        observation_without_component = self._clone_observation(self.branch_dev, "Title", "")
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(observation_without_component)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_no_propagate_branches_configured(self, save_assessment_mock) -> None:
        self.product.propagate_branches = None
        self.product.save()
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(Observation.objects.get(pk=self.new_observation.pk))

        save_assessment_mock.assert_not_called()


class TestPropagationEndToEnd(BasePropagationTestCase):
    @patch("application.core.services.observation_log.send_observation_title_notification")
    @patch("application.core.services.observation_log.send_observation_notification")
    @patch("application.core.services.observation_log.get_current_user")
    @patch("application.core.services.assessment.get_current_user")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    def test_propagate_assessment_creates_auto_approved_log(  # pylint: disable=too-many-positional-arguments
        self,
        check_security_gate_mock,
        push_observation_to_issue_tracker_mock,
        get_current_user_assessment_mock,
        get_current_user_observation_log_mock,
        send_observation_notification_mock,
        send_observation_title_notification_mock,
    ) -> None:
        get_current_user_assessment_mock.return_value = self.user
        get_current_user_observation_log_mock.return_value = self.user

        # propagated assessments must be auto approved even if assessments need approval
        self.product.assessments_need_approval = True
        self.product.save()

        target_observation = self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)

        propagate_assessment(source_log)

        target_observation.refresh_from_db()
        self.assertEqual(Severity.SEVERITY_HIGH, target_observation.current_severity)
        self.assertEqual(Status.STATUS_FALSE_POSITIVE, target_observation.current_status)

        target_logs = Observation_Log.objects.filter(observation=target_observation)
        self.assertEqual(1, target_logs.count())
        target_log = target_logs.first()
        self.assertEqual(source_log, target_log.propagated_from)
        self.assertEqual(Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED, target_log.assessment_status)
        self.assertEqual(Severity.SEVERITY_HIGH, target_log.severity)
        self.assertEqual(Status.STATUS_FALSE_POSITIVE, target_log.status)

        # source log and one propagated log, no re-propagation has happened
        self.assertEqual(2, Observation_Log.objects.count())

    @patch("application.core.services.observation_log.send_observation_title_notification")
    @patch("application.core.services.observation_log.send_observation_notification")
    @patch("application.core.services.observation_log.get_current_user")
    @patch("application.core.services.assessment.get_current_user")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    def test_set_propagated_assessment_for_new_observation_end_to_end(  # pylint: disable=too-many-positional-arguments
        self,
        check_security_gate_mock,
        push_observation_to_issue_tracker_mock,
        get_current_user_assessment_mock,
        get_current_user_observation_log_mock,
        send_observation_notification_mock,
        send_observation_title_notification_mock,
    ) -> None:
        get_current_user_assessment_mock.return_value = self.user
        get_current_user_observation_log_mock.return_value = self.user

        observation_main = self._clone_observation(self.branch_main)
        candidate_log = self._create_log(observation_main, severity=Severity.SEVERITY_HIGH)

        new_branch = self._create_branch("db_branch_internal_new")
        new_observation = self._clone_observation(new_branch)

        set_propagated_assessment_for_new_observation(new_observation)

        new_observation.refresh_from_db()
        self.assertEqual(Severity.SEVERITY_HIGH, new_observation.current_severity)
        self.assertEqual(Status.STATUS_FALSE_POSITIVE, new_observation.current_status)

        new_logs = Observation_Log.objects.filter(observation=new_observation)
        self.assertEqual(1, new_logs.count())
        new_log = new_logs.first()
        self.assertEqual(candidate_log, new_log.propagated_from)
        self.assertEqual(Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED, new_log.assessment_status)
