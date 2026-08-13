import unittest
from unittest.mock import MagicMock, call, patch

from application.core.models import Observation, Product
from application.import_observations.models import Parser
from application.rules.models import Rule
from application.rules.services.simulator import (
    MAX_OBSERVATIONS,
    _get_observations,
    simulate_rule,
)
from application.rules.types import Rule_Type

# Page size of the Paginator in simulate_rule, used to build data sets spanning multiple pages
PAGE_SIZE = 1000


class ObservationList(list):
    """
    Minimal QuerySet stand-in for the observations returned by _get_observations.
    Supports everything Django's Paginator needs: len(), slicing and count().
    """

    def count(self) -> int:
        return len(self)


class TestGetObservations(unittest.TestCase):
    def setUp(self):
        self.product = Product(id=1, name="product")
        self.parser = Parser(id=1, name="parser")

        self.rule = Rule(name="rule", type=Rule_Type.RULE_TYPE_FIELDS)

    def _mock_queryset(self):
        queryset = MagicMock(name="queryset")
        queryset.filter.return_value = queryset
        queryset.order_by.return_value = queryset
        queryset.select_related.return_value = queryset
        return queryset

    # --- product selection ---

    @patch("application.rules.services.simulator.Observation.objects")
    def test_product(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.product = self.product

        observations = _get_observations(self.rule)

        self.assertEqual(observations, queryset)
        mock_objects.filter.assert_called_once_with(product=self.product)

    @patch("application.rules.services.simulator.Observation.objects")
    def test_product_group(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        # The products of a product group can only be read from the database, so the rule has to be mocked
        product_group = MagicMock(spec=Product)
        product_group.is_product_group = True
        rule = MagicMock(spec=Rule)
        rule.type = Rule_Type.RULE_TYPE_FIELDS
        rule.product = product_group
        rule.parser = None
        rule.scanner_prefix = ""

        observations = _get_observations(rule)

        self.assertEqual(observations, queryset)
        mock_objects.filter.assert_called_once_with(product__in=product_group.products.all())

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_general_rule(self, mock_objects, mock_get_products):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        mock_get_products.return_value = [self.product]

        observations = _get_observations(self.rule)

        self.assertEqual(observations, queryset)
        mock_get_products.assert_called_once_with()
        mock_objects.filter.assert_called_once_with(product__in=[self.product], product__apply_general_rules=True)

    # --- parser and scanner prefix ---

    @patch("application.rules.services.simulator.Observation.objects")
    def test_no_parser_and_no_scanner_prefix(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.product = self.product

        _get_observations(self.rule)

        queryset.filter.assert_not_called()

    @patch("application.rules.services.simulator.Observation.objects")
    def test_parser(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.product = self.product
        self.rule.parser = self.parser

        _get_observations(self.rule)

        queryset.filter.assert_called_once_with(parser=self.parser)

    @patch("application.rules.services.simulator.Observation.objects")
    def test_scanner_prefix(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.product = self.product
        self.rule.scanner_prefix = "scanner_prefix"

        _get_observations(self.rule)

        queryset.filter.assert_called_once_with(scanner__startswith="scanner_prefix")

    @patch("application.rules.services.simulator.Observation.objects")
    def test_parser_and_scanner_prefix(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.product = self.product
        self.rule.parser = self.parser
        self.rule.scanner_prefix = "scanner_prefix"

        _get_observations(self.rule)

        queryset.filter.assert_has_calls(
            [
                call(parser=self.parser),
                call(scanner__startswith="scanner_prefix"),
            ]
        )

    @patch("application.rules.services.simulator.Observation.objects")
    def test_parser_and_scanner_prefix_for_rego_rule(self, mock_objects):
        """Rego rules support parser and scanner prefix as well, so both are filtered in the database."""
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.type = Rule_Type.RULE_TYPE_REGO
        self.rule.product = self.product
        self.rule.parser = self.parser
        self.rule.scanner_prefix = "scanner_prefix"

        _get_observations(self.rule)

        queryset.filter.assert_has_calls(
            [
                call(parser=self.parser),
                call(scanner__startswith="scanner_prefix"),
            ]
        )

    # --- ordering and prefetching ---

    @patch("application.rules.services.simulator.Observation.objects")
    def test_order_by_and_select_related(self, mock_objects):
        queryset = self._mock_queryset()
        mock_objects.filter.return_value = queryset
        self.rule.product = self.product

        _get_observations(self.rule)

        queryset.order_by.assert_called_once_with("product__name", "title")
        queryset.select_related.assert_has_calls(
            [
                call("product"),
                call("product__product_group"),
                call("branch"),
                call("origin_service"),
                call("parser"),
                call("general_rule"),
                call("product_rule"),
            ]
        )


class TestSimulateRule(unittest.TestCase):
    def setUp(self):
        self.product = Product(id=1, name="product")
        self.rule = Rule(name="rule", type=Rule_Type.RULE_TYPE_FIELDS, product=self.product)

        self.mock_get_observations = self._patch("application.rules.services.simulator._get_observations")
        self.mock_rule_engine = self._patch("application.rules.services.simulator.Rule_Engine")
        self.mock_check_rule = self.mock_rule_engine.return_value.check_rule_for_observation

    def _patch(self, target: str) -> MagicMock:
        patcher = patch(target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _observations(self, number: int, product: Product = None) -> ObservationList:
        product = product if product else self.product
        return ObservationList(
            Observation(title=f"observation_{number_observation}", product=product)
            for number_observation in range(number)
        )

    # --- results ---

    def test_no_observations(self):
        self.mock_get_observations.return_value = ObservationList()

        simulation_results = simulate_rule(self.rule)

        self.assertEqual(simulation_results, [])
        self.mock_rule_engine.assert_not_called()

    def test_all_observations_match(self):
        observations = self._observations(3)
        self.mock_get_observations.return_value = observations
        self.mock_check_rule.return_value = True

        simulation_results = simulate_rule(self.rule)

        self.assertEqual(simulation_results, list(observations))

    def test_no_observation_matches(self):
        self.mock_get_observations.return_value = self._observations(3)
        self.mock_check_rule.return_value = False

        simulation_results = simulate_rule(self.rule)

        self.assertEqual(simulation_results, [])

    def test_some_observations_match(self):
        observations = self._observations(3)
        self.mock_get_observations.return_value = observations
        self.mock_check_rule.side_effect = [True, False, True]

        simulation_results = simulate_rule(self.rule)

        self.assertEqual(simulation_results, [observations[0], observations[2]])

    def test_observations_are_not_copied_into_results(self):
        observations = self._observations(1)
        self.mock_get_observations.return_value = observations
        self.mock_check_rule.return_value = True

        simulation_results = simulate_rule(self.rule)

        self.assertIs(simulation_results[0], observations[0])

    # --- pagination and maximum number of results ---

    def test_all_pages_are_processed(self):
        self.mock_get_observations.return_value = self._observations(2 * PAGE_SIZE + 500)
        self.mock_check_rule.return_value = False

        simulation_results = simulate_rule(self.rule)

        self.assertEqual(simulation_results, [])
        self.assertEqual(self.mock_check_rule.call_count, 2 * PAGE_SIZE + 500)

    def test_maximum_number_of_results(self):
        observations = self._observations(MAX_OBSERVATIONS + 50)
        self.mock_get_observations.return_value = observations
        self.mock_check_rule.return_value = True

        simulation_results = simulate_rule(self.rule)

        self.assertEqual(simulation_results, list(observations)[:MAX_OBSERVATIONS])
        # Processing stops as soon as the maximum number of results has been reached
        self.assertEqual(self.mock_check_rule.call_count, MAX_OBSERVATIONS)

    def test_maximum_number_of_results_on_later_page(self):
        first_match = PAGE_SIZE + 500
        observations = self._observations(2 * PAGE_SIZE)
        self.mock_get_observations.return_value = observations
        self.mock_check_rule.side_effect = (index >= first_match for index in range(2 * PAGE_SIZE))

        simulation_results = simulate_rule(self.rule)

        last_match = first_match + MAX_OBSERVATIONS
        self.assertEqual(simulation_results, list(observations)[first_match:last_match])
        # The remaining observations of the page are not processed anymore
        self.assertEqual(self.mock_check_rule.call_count, last_match)

    # --- rule engines ---

    def test_rule_engine_is_reused_per_product(self):
        product_2 = Product(id=2, name="product_2")
        observations = self._observations(2) + self._observations(2, product_2) + self._observations(1)
        self.mock_get_observations.return_value = ObservationList(observations)
        self.mock_check_rule.return_value = False

        simulate_rule(self.rule)

        self.assertEqual(self.mock_rule_engine.call_count, 2)
        self.mock_rule_engine.assert_has_calls([call(self.product), call(product_2)], any_order=True)

    # --- rule engine call ---

    def test_check_rule_for_observation_parameters(self):
        observations = self._observations(1)
        self.mock_get_observations.return_value = observations
        self.mock_check_rule.return_value = True

        simulate_rule(self.rule)

        self.mock_check_rule.assert_called_once()
        arguments = self.mock_check_rule.call_args.args
        self.assertEqual(arguments[0], self.rule)
        self.assertIs(arguments[1], observations[0])
        # A simulation does not need an observation before the rule has been applied
        self.assertIsNone(arguments[2])
        self.assertTrue(arguments[3])
