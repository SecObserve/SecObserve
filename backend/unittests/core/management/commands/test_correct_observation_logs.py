from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from application.access_control.models import User
from application.core.models import Observation, Observation_Log, Product
from application.import_observations.models import Parser
from application.rules.models import Rule


class TestCorrectObservationLogsCommand(TestCase):
    """DB-backed tests for the `correct_observation_logs` management command.

    The command nulls out any of the four rule foreign keys on an
    Observation_Log whose linked rule's `description` does not match the log's
    `comment`, leaving matching (and unset) rules untouched.
    """

    def setUp(self) -> None:
        self.user = User.objects.create(username="correct-logs@example.com")
        self.product = Product.objects.create(name="product_1")
        self.parser = Parser.objects.create(name="parser_1")
        self.observation = Observation.objects.create(
            title="observation_1",
            product=self.product,
            parser=self.parser,
            numerical_severity=1,
            import_last_seen=timezone.now(),
        )

    def _create_rule(self, name: str, description: str) -> Rule:
        return Rule.objects.create(name=name, description=description)

    def _create_log(self, comment: str, **rule_fields: Rule) -> Observation_Log:
        return Observation_Log.objects.create(
            observation=self.observation,
            user=self.user,
            comment=comment,
            **rule_fields,
        )

    def test_rule_kept_when_comment_matches_description(self) -> None:
        rule = self._create_rule("rule_match", "matching description")
        log = self._create_log("matching description", product_rule=rule)

        call_command("correct_observation_logs")

        log.refresh_from_db()
        self.assertEqual(rule, log.product_rule)

    def test_rule_nulled_when_comment_differs(self) -> None:
        rule = self._create_rule("rule_mismatch", "some description")
        log = self._create_log("a different comment", general_rule=rule)

        call_command("correct_observation_logs")

        log.refresh_from_db()
        self.assertIsNone(log.general_rule)

    def test_all_four_rule_types_are_corrected_independently(self) -> None:
        comment = "the same comment"
        # Two rules match the comment (kept), two do not (nulled).
        general_rule = self._create_rule("general_rule", comment)
        product_rule = self._create_rule("product_rule", "different")
        general_rule_rego = self._create_rule("general_rule_rego", "different")
        product_rule_rego = self._create_rule("product_rule_rego", comment)

        log = self._create_log(
            comment,
            general_rule=general_rule,
            product_rule=product_rule,
            general_rule_rego=general_rule_rego,
            product_rule_rego=product_rule_rego,
        )

        call_command("correct_observation_logs")

        log.refresh_from_db()
        self.assertEqual(general_rule, log.general_rule)
        self.assertIsNone(log.product_rule)
        self.assertIsNone(log.general_rule_rego)
        self.assertEqual(product_rule_rego, log.product_rule_rego)

    def test_log_without_any_rule_is_untouched(self) -> None:
        log = self._create_log("just a comment")

        call_command("correct_observation_logs")

        log.refresh_from_db()
        self.assertIsNone(log.general_rule)
        self.assertIsNone(log.product_rule)
        self.assertIsNone(log.general_rule_rego)
        self.assertIsNone(log.product_rule_rego)
        self.assertEqual("just a comment", log.comment)

    @patch("application.core.management.commands.correct_observation_logs.logger")
    def test_corrected_count_is_logged(self, mock_logger) -> None:
        # One log to be corrected, one to be kept.
        self._create_log("a comment", general_rule=self._create_rule("r1", "different"))
        self._create_log("keep me", product_rule=self._create_rule("r2", "keep me"))

        call_command("correct_observation_logs")

        mock_logger.info.assert_any_call("... %s Observation Logs corrected", 1)
        mock_logger.error.assert_not_called()
