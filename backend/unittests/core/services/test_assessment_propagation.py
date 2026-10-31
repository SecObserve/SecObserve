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
    propagate_assessment_removal,
    remove_assessment,
    save_assessment,
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

    @staticmethod
    def _clear_component(observation: Observation) -> Observation:
        # the name and the version have to be cleared as well, otherwise the pre_save
        # normalization derives origin_component_name_version from them again
        observation.origin_component_name_version = ""
        observation.origin_component_name = ""
        observation.origin_component_version = ""
        observation.save()
        return observation

    def _make_observation_dev_source_only(self) -> None:
        # a SAST / secrets finding: no component, but a source file with line numbers
        observation = self._clear_component(Observation.objects.get(pk=1))
        observation.origin_source_file = "src/main.py"
        observation.origin_source_line_start = 10
        observation.origin_source_line_end = 12
        observation.save()
        self.observation_dev = Observation.objects.get(pk=1)

    def _clone_observation(  # pylint: disable=too-many-arguments
        self,
        branch: Optional[Branch],
        title: Optional[str] = None,
        origin_component_name_version: Optional[str] = None,
        *,
        origin_source_file: Optional[str] = None,
        origin_source_line_start: Optional[int] = None,
        origin_source_line_end: Optional[int] = None,
    ) -> Observation:
        observation = Observation.objects.get(pk=1)
        observation.pk = None
        observation.branch = branch
        if title is not None:
            observation.title = title
        if origin_component_name_version is not None:
            observation.origin_component_name_version = origin_component_name_version
        if origin_source_file is not None:
            observation.origin_source_file = origin_source_file
        if origin_source_line_start is not None:
            observation.origin_source_line_start = origin_source_line_start
        if origin_source_line_end is not None:
            observation.origin_source_line_end = origin_source_line_end
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
            new_priority_changed=False,
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
    def test_not_propagated_with_only_new_observation(self, save_assessment_mock) -> None:
        self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)
        source_log.observation.product.propagate_branches_new_assessment = False
        source_log.observation.product.propagate_branches_new_observation = True

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
    def test_observation_without_component_and_source_file(self, save_assessment_mock) -> None:
        # both observations have neither a component nor a source file, so only the
        # guard can prevent the propagation
        observation_without_identity = self._clear_component(self._clone_observation(self.branch_dev))
        self._clear_component(self._clone_observation(self.branch_main))
        source_log = self._create_log(observation_without_identity)

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

    @patch("application.core.services.assessment.save_assessment")
    def test_propagates_to_multiple_matching_branches(self, save_assessment_mock) -> None:
        second_branch = self._create_branch("db_branch_internal_second")
        target_observation_1 = self._clone_observation(self.branch_main)
        target_observation_2 = self._clone_observation(second_branch)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        self.assertEqual(2, save_assessment_mock.call_count)
        self.assertEqual(
            {target_observation_1, target_observation_2},
            {call.kwargs["observation"] for call in save_assessment_mock.call_args_list},
        )

    @patch("application.core.services.assessment.save_assessment")
    def test_branch_matching_several_patterns_propagated_once(self, save_assessment_mock) -> None:
        self.product.propagate_branches = [{"propagate_to": "db_branch_internal_.*"}, {"propagate_to": "db_branch_.*"}]
        self.product.save()
        self._clone_observation(self.branch_main)
        source_log = self._create_log(Observation.objects.get(pk=1))

        propagate_assessment(source_log)

        save_assessment_mock.assert_called_once()

    @patch("application.core.services.assessment.save_assessment")
    def test_propagates_source_only_observation(self, save_assessment_mock) -> None:
        self._make_observation_dev_source_only()
        target_observation = self._clone_observation(self.branch_main)
        source_log = self._create_log(self.observation_dev, severity=Severity.SEVERITY_HIGH)

        propagate_assessment(source_log)

        save_assessment_mock.assert_called_once_with(
            observation=target_observation,
            new_severity=Severity.SEVERITY_HIGH,
            new_status=Status.STATUS_FALSE_POSITIVE,
            new_priority=None,
            new_priority_changed=False,
            comment="manual assessment",
            new_vex_justification="",
            new_vex_remediations=None,
            new_risk_acceptance_expiry_date=None,
            propagated_from=source_log,
        )

    @patch("application.core.services.assessment.save_assessment")
    def test_different_origin_source_file_not_propagated(self, save_assessment_mock) -> None:
        self._make_observation_dev_source_only()
        self._clone_observation(self.branch_main, origin_source_file="src/other.py")
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_different_origin_source_line_start_not_propagated(self, save_assessment_mock) -> None:
        self._make_observation_dev_source_only()
        self._clone_observation(self.branch_main, origin_source_line_start=20)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_different_origin_source_line_end_not_propagated(self, save_assessment_mock) -> None:
        self._make_observation_dev_source_only()
        self._clone_observation(self.branch_main, origin_source_line_end=22)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_source_file_only_on_target_not_propagated(self, save_assessment_mock) -> None:
        # the source observation has a component but no source file, the target has both:
        # all origin fields have to match, not just the component
        self._clone_observation(self.branch_main, origin_source_file="src/main.py", origin_source_line_start=10)
        source_log = self._create_log(self.observation_dev)

        propagate_assessment(source_log)

        save_assessment_mock.assert_not_called()


class TestPropagateAssessmentRemoval(BasePropagationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.source_log = self._create_log(self.observation_dev, created=timezone.now() - timedelta(hours=3))
        self.removal_log = self._create_log(
            self.observation_dev,
            status="",
            comment="assessment removed",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED,
        )

    def _clone_with_copy(self, branch: Branch, original: Observation_Log) -> Observation:
        observation = self._clone_observation(branch)
        self._create_log(observation, propagated_from=original, created=timezone.now() - timedelta(hours=2))
        return observation

    @patch("application.core.services.assessment.remove_assessment")
    def test_removes_copy_on_matching_branch(self, remove_assessment_mock) -> None:
        target_observation = self._clone_with_copy(self.branch_main, self.source_log)

        propagate_assessment_removal(self.removal_log, self.source_log.pk)

        remove_assessment_mock.assert_called_once_with(
            target_observation, "assessment removed", propagated_from=self.removal_log
        )

    @patch("application.core.services.assessment.remove_assessment")
    def test_removes_original_and_copies_of_same_original(self, remove_assessment_mock) -> None:
        # the removed assessment on dev is itself a copy of the original on release
        observation_release = self._clone_observation(self._create_branch("db_branch_internal_release"))
        original_log = self._create_log(observation_release, created=timezone.now() - timedelta(hours=4))
        target_observation = self._clone_with_copy(self.branch_main, original_log)

        propagate_assessment_removal(self.removal_log, original_log.pk)

        self.assertEqual(
            {observation_release, target_observation},
            {call.args[0] for call in remove_assessment_mock.call_args_list},
        )

    @patch("application.core.services.assessment.remove_assessment")
    def test_keeps_independent_assessment(self, remove_assessment_mock) -> None:
        self._create_log(self._clone_observation(self.branch_main))

        propagate_assessment_removal(self.removal_log, self.source_log.pk)

        remove_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.remove_assessment")
    def test_keeps_assessment_changed_after_copy(self, remove_assessment_mock) -> None:
        target_observation = self._clone_with_copy(self.branch_main, self.source_log)
        self._create_log(target_observation, status=Status.STATUS_OPEN, created=timezone.now() - timedelta(hours=1))

        propagate_assessment_removal(self.removal_log, self.source_log.pk)

        remove_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.remove_assessment")
    def test_not_propagated_without_propagation_flags(self, remove_assessment_mock) -> None:
        self._clone_with_copy(self.branch_main, self.source_log)
        self.removal_log.observation.product.propagate_branches_new_assessment = False
        self.removal_log.observation.product.propagate_branches_new_observation = False

        propagate_assessment_removal(self.removal_log, self.source_log.pk)

        remove_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.remove_assessment")
    def test_propagate_branches_new_observation_only(self, remove_assessment_mock) -> None:
        # the copy can have been applied to a new observation, it has to be removed as well
        target_observation = self._clone_with_copy(self.branch_main, self.source_log)
        self.removal_log.observation.product.propagate_branches_new_assessment = False
        self.removal_log.observation.product.propagate_branches_new_observation = True

        propagate_assessment_removal(self.removal_log, self.source_log.pk)

        remove_assessment_mock.assert_called_once_with(
            target_observation, "assessment removed", propagated_from=self.removal_log
        )

    @patch("application.core.services.assessment.remove_assessment")
    def test_propagate_branches_new_observation_only_product_group(self, remove_assessment_mock) -> None:
        self._configure_product_group_propagation_only(new_assessment=False, new_observation=True)
        target_observation = self._clone_with_copy(self.branch_main, self.source_log)

        propagate_assessment_removal(Observation_Log.objects.get(pk=self.removal_log.pk), self.source_log.pk)

        remove_assessment_mock.assert_called_once()
        self.assertEqual(target_observation, remove_assessment_mock.call_args.args[0])

    @patch("application.core.services.assessment.remove_assessment")
    def test_not_propagated_without_propagation_flags_product_group(self, remove_assessment_mock) -> None:
        self._configure_product_group_propagation_only(new_assessment=False, new_observation=False)
        self._clone_with_copy(self.branch_main, self.source_log)

        propagate_assessment_removal(Observation_Log.objects.get(pk=self.removal_log.pk), self.source_log.pk)

        remove_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.remove_assessment")
    def test_target_branch_not_matching(self, remove_assessment_mock) -> None:
        self._clone_with_copy(self._create_branch("feature_x"), self.source_log)

        propagate_assessment_removal(self.removal_log, self.source_log.pk)

        remove_assessment_mock.assert_not_called()


class TestSetPropagatedAssessmentForNewObservation(BasePropagationTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.new_branch = self._create_branch("db_branch_internal_new")
        self.new_observation = self._clone_observation(self.new_branch)
        self.observation_main = self._clone_observation(self.branch_main)

    def _switch_to_source_only(self) -> None:
        # rebuild both observations as source-only findings, the clones of setUp still
        # carry the component of the base test case
        self.new_observation.delete()
        self.observation_main.delete()
        self._make_observation_dev_source_only()
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
            new_priority_changed=False,
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
    def test_removed_assessment_not_applied(self, save_assessment_mock) -> None:
        self._create_log(self.observation_main, created=timezone.now() - timedelta(hours=2))
        self._create_log(
            self.observation_main,
            status="",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED,
            created=timezone.now() - timedelta(hours=1),
        )

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_expired_risk_acceptance_not_applied(self, save_assessment_mock) -> None:
        self._create_log(
            self.observation_main, status=Status.STATUS_RISK_ACCEPTED, created=timezone.now() - timedelta(hours=2)
        )
        self._create_log(
            self.observation_main,
            status="",
            comment="Risk acceptance has expired.",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED,
            created=timezone.now() - timedelta(hours=1),
        )

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_removal_wins_over_older_assessment_of_other_branch(self, save_assessment_mock) -> None:
        observation_release = self._clone_observation(self._create_branch("db_branch_internal_release"))
        self._create_log(observation_release, created=timezone.now() - timedelta(hours=2))
        self._create_log(
            self.observation_main,
            status="",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED,
            created=timezone.now() - timedelta(hours=1),
        )

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_assessment_after_removal_applied(self, save_assessment_mock) -> None:
        self._create_log(
            self.observation_main,
            status="",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED,
            created=timezone.now() - timedelta(hours=2),
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
    def test_observation_without_component_and_source_file(self, save_assessment_mock) -> None:
        # both observations have neither a component nor a source file, so only the
        # guard can prevent the propagation
        observation_without_identity = self._clear_component(self._clone_observation(self.branch_dev))
        self._create_log(self._clear_component(self.observation_main))

        set_propagated_assessment_for_new_observation(observation_without_identity)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_no_propagate_branches_configured(self, save_assessment_mock) -> None:
        self.product.propagate_branches = None
        self.product.save()
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(Observation.objects.get(pk=self.new_observation.pk))

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_applies_assessment_of_source_only_observation(self, save_assessment_mock) -> None:
        self._switch_to_source_only()
        candidate_log = self._create_log(self.observation_main, severity=Severity.SEVERITY_HIGH)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_called_once_with(
            observation=self.new_observation,
            new_severity=Severity.SEVERITY_HIGH,
            new_status=Status.STATUS_FALSE_POSITIVE,
            new_priority=None,
            new_priority_changed=False,
            comment="manual assessment",
            new_vex_justification="",
            new_vex_remediations=None,
            new_risk_acceptance_expiry_date=None,
            propagated_from=candidate_log,
        )

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_with_different_origin_source_file(self, save_assessment_mock) -> None:
        self._switch_to_source_only()
        self.observation_main.origin_source_file = "src/other.py"
        self.observation_main.save()
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_with_different_origin_source_line_start(self, save_assessment_mock) -> None:
        self._switch_to_source_only()
        self.observation_main.origin_source_line_start = 20
        self.observation_main.save()
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_with_different_origin_source_line_end(self, save_assessment_mock) -> None:
        self._switch_to_source_only()
        self.observation_main.origin_source_line_end = 22
        self.observation_main.save()
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(self.new_observation)

        save_assessment_mock.assert_not_called()

    @patch("application.core.services.assessment.save_assessment")
    def test_excludes_logs_with_source_file_only_on_candidate(self, save_assessment_mock) -> None:
        # the new observation has a component but no source file, the candidate has both:
        # all origin fields have to match, not just the component
        self.observation_main.origin_source_file = "src/main.py"
        self.observation_main.origin_source_line_start = 10
        self.observation_main.save()
        self._create_log(self.observation_main)

        set_propagated_assessment_for_new_observation(self.new_observation)

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

    @patch("application.core.services.observation_log.send_observation_title_notification")
    @patch("application.core.services.observation_log.send_observation_notification")
    @patch("application.core.services.observation_log.get_current_user")
    @patch("application.core.services.assessment.get_current_user")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    def test_propagate_assessment_removal_end_to_end(  # pylint: disable=too-many-positional-arguments
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

        target_observation = self._clone_observation(self.branch_main)
        status_before_assessment = target_observation.current_status
        save_assessment(
            observation=self.observation_dev,
            new_severity="",
            new_status=Status.STATUS_NOT_AFFECTED,
            new_priority=None,
            new_priority_changed=False,
            comment="vulnerable function is not used",
            new_vex_justification="",
            new_vex_remediations=None,
            new_risk_acceptance_expiry_date=None,
        )
        target_observation.refresh_from_db()
        self.assertEqual(Status.STATUS_NOT_AFFECTED, target_observation.current_status)

        removal_log = remove_assessment(
            Observation.objects.get(pk=self.observation_dev.pk), "vulnerable function is used now"
        )

        target_observation.refresh_from_db()
        self.assertEqual("", target_observation.assessment_status)
        self.assertEqual(status_before_assessment, target_observation.current_status)

        target_removal_log = Observation_Log.objects.get(
            observation=target_observation, assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED
        )
        self.assertEqual(removal_log, target_removal_log.propagated_from)
        self.assertEqual("vulnerable function is used now", target_removal_log.comment)

        # assessment and removal on both branches, no re-propagation has happened
        self.assertEqual(4, Observation_Log.objects.count())

    @patch("application.core.services.observation_log.send_observation_title_notification")
    @patch("application.core.services.observation_log.send_observation_notification")
    @patch("application.core.services.observation_log.get_current_user")
    @patch("application.core.services.assessment.get_current_user")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    def test_propagate_assessment_removal_to_new_observation_end_to_end(  # pylint: disable=too-many-positional-arguments
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

        # assessments only reach new observations
        self.product.propagate_branches_new_assessment = False
        self.product.propagate_branches_new_observation = True
        self.product.save()

        # cloned before the assessment, otherwise the clone would copy it
        new_observation = self._clone_observation(self.branch_main)
        status_before_assessment = new_observation.current_status

        save_assessment(
            observation=Observation.objects.get(pk=self.observation_dev.pk),
            new_severity="",
            new_status=Status.STATUS_NOT_AFFECTED,
            new_priority=None,
            new_priority_changed=False,
            comment="vulnerable function is not used",
            new_vex_justification="",
            new_vex_remediations=None,
            new_risk_acceptance_expiry_date=None,
        )
        new_observation.refresh_from_db()
        self.assertEqual(status_before_assessment, new_observation.current_status)

        set_propagated_assessment_for_new_observation(Observation.objects.get(pk=new_observation.pk))
        new_observation.refresh_from_db()
        self.assertEqual(Status.STATUS_NOT_AFFECTED, new_observation.current_status)

        removal_log = remove_assessment(
            Observation.objects.get(pk=self.observation_dev.pk), "vulnerable function is used now"
        )

        new_observation.refresh_from_db()
        self.assertEqual("", new_observation.assessment_status)
        self.assertEqual(status_before_assessment, new_observation.current_status)

        new_removal_log = Observation_Log.objects.get(
            observation=new_observation, assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED
        )
        self.assertEqual(removal_log, new_removal_log.propagated_from)

        # assessment and removal on both branches, no re-propagation has happened
        self.assertEqual(4, Observation_Log.objects.count())
