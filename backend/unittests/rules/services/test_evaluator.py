import unittest
from unittest.mock import MagicMock, call, patch

from django.db.models import Q

from application.core.models import Observation, Product
from application.import_observations.models import Parser
from application.rules.models import Rule
from application.rules.services.evaluator import (
    EvaluationResult,
    _get_affected_observation_pks,
    evaluate_general_rule,
    general_rule_evaluation_requested,
    request_general_rule_evaluation,
)
from application.rules.types import Rule_Type


class TestGetAffectedObservationPks(unittest.TestCase):
    def setUp(self):
        self.parser = Parser(id=1, name="parser")
        self.rule = Rule(id=1, name="rule", type=Rule_Type.RULE_TYPE_FIELDS)

    @patch("application.rules.services.evaluator.Observation.objects")
    def test_scope_and_linked_observations(self, mock_objects):
        mock_objects.filter.return_value.values_list.return_value = [1, 2, 3]

        pks = _get_affected_observation_pks(self.rule)

        self.assertEqual(pks, [1, 2, 3])
        expected_query = Q(product__apply_general_rules=True) | (
            Q(general_rule=self.rule) | Q(general_rule_rego=self.rule)
        )
        mock_objects.filter.assert_called_once_with(expected_query)
        mock_objects.filter.return_value.values_list.assert_called_once_with("pk", flat=True)

    @patch("application.rules.services.evaluator.Observation.objects")
    def test_parser_and_scanner_prefix_narrow_only_the_scope(self, mock_objects):
        """Linked observations outside the parser/scanner scope must still be reverted."""
        mock_objects.filter.return_value.values_list.return_value = []
        self.rule.parser = self.parser
        self.rule.scanner_prefix = "scanner_prefix"

        _get_affected_observation_pks(self.rule)

        expected_query = (
            Q(product__apply_general_rules=True) & Q(parser=self.parser) & Q(scanner__startswith="scanner_prefix")
        ) | (Q(general_rule=self.rule) | Q(general_rule_rego=self.rule))
        mock_objects.filter.assert_called_once_with(expected_query)


class TestEvaluateGeneralRule(unittest.TestCase):
    def setUp(self):
        self.product = Product(id=1, name="product", apply_general_rules=True)
        self.rule = Rule(id=1, name="rule", type=Rule_Type.RULE_TYPE_FIELDS)

        self.mock_get_pks = self._patch("application.rules.services.evaluator._get_affected_observation_pks")
        self.mock_objects = self._patch("application.rules.services.evaluator.Observation.objects")
        self.mock_rule_engine = self._patch("application.rules.services.evaluator.Rule_Engine")
        self.mock_apply_rules = self.mock_rule_engine.return_value.apply_rules_for_observation
        self.mock_check_security_gate = self._patch("application.rules.services.evaluator.check_security_gate")

    def _patch(self, target: str) -> MagicMock:
        patcher = patch(target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _observations(self, number: int, product: Product = None) -> list[Observation]:
        product = product if product else self.product
        return [
            Observation(title=f"observation_{number_observation}", product=product)
            for number_observation in range(number)
        ]

    def _mock_chunks(self, *chunks: list[Observation]) -> None:
        querysets = []
        for chunk in chunks:
            queryset = MagicMock(name="queryset")
            queryset.select_related.return_value = queryset
            queryset.__iter__.side_effect = lambda chunk=chunk: iter(chunk)
            querysets.append(queryset)
        self.mock_objects.filter.side_effect = querysets
        self.mock_get_pks.return_value = [pk for chunk in chunks for pk in range(len(chunk))]

    # --- results and rule engine calls ---

    def test_no_affected_observations(self):
        self.mock_get_pks.return_value = []

        result = evaluate_general_rule(self.rule)

        self.assertEqual(result, EvaluationResult(observations_processed=0, observations_changed=0))
        self.mock_rule_engine.assert_not_called()
        self.mock_check_security_gate.assert_not_called()

    def test_full_rule_engine_pass_for_every_observation(self):
        observations = self._observations(3)
        self._mock_chunks(observations)

        result = evaluate_general_rule(self.rule)

        self.assertEqual(result.observations_processed, 3)
        self.mock_apply_rules.assert_has_calls([call(observation) for observation in observations])

    def test_rule_engine_is_reused_per_product(self):
        product_2 = Product(id=2, name="product_2", apply_general_rules=True)
        observations = self._observations(2) + self._observations(2, product_2) + self._observations(1)
        self._mock_chunks(observations)

        evaluate_general_rule(self.rule)

        self.assertEqual(self.mock_rule_engine.call_count, 2)
        self.mock_rule_engine.assert_has_calls([call(self.product), call(product_2)], any_order=True)

    # --- change detection and security gate ---

    def test_no_changes(self):
        self._mock_chunks(self._observations(3))

        result = evaluate_general_rule(self.rule)

        self.assertEqual(result, EvaluationResult(observations_processed=3, observations_changed=0))
        self.mock_check_security_gate.assert_not_called()

    def test_changed_observations_are_counted(self):
        observations = self._observations(3)
        self._mock_chunks(observations)

        def apply_rules(observation: Observation) -> None:
            if observation is not observations[1]:
                observation.rule_severity = "Critical"
                observation.current_severity = "Critical"

        self.mock_apply_rules.side_effect = apply_rules

        result = evaluate_general_rule(self.rule)

        self.assertEqual(result, EvaluationResult(observations_processed=3, observations_changed=2))

    def test_security_gate_is_checked_once_per_product_with_changes(self):
        product_2 = Product(id=2, name="product_2", apply_general_rules=True)
        observations = self._observations(2) + self._observations(1, product_2)
        self._mock_chunks(observations)

        def apply_rules(observation: Observation) -> None:
            if observation.product == self.product:
                observation.rule_status = "False positive"

        self.mock_apply_rules.side_effect = apply_rules

        evaluate_general_rule(self.rule)

        self.mock_check_security_gate.assert_called_once_with(self.product)

    # --- chunking ---

    @patch("application.rules.services.evaluator.CHUNK_SIZE", 2)
    def test_observations_are_fetched_in_chunks_of_the_initial_pks(self):
        self._mock_chunks(self._observations(2), self._observations(1))
        self.mock_get_pks.return_value = [1, 2, 3]

        result = evaluate_general_rule(self.rule)

        self.assertEqual(result.observations_processed, 3)
        self.mock_objects.filter.assert_has_calls([call(pk__in=(1, 2)), call(pk__in=(3,))])


class TestRequestGeneralRuleEvaluation(unittest.TestCase):
    def test_signal_is_sent_with_the_rule_id(self):
        received = []

        def dummy_receiver(sender, rule_id, **kwargs):  # pylint: disable=unused-argument
            received.append((sender, rule_id))

        general_rule_evaluation_requested.connect(dummy_receiver)
        self.addCleanup(general_rule_evaluation_requested.disconnect, dummy_receiver)

        request_general_rule_evaluation(1)

        self.assertEqual(received, [(Rule, 1)])
