import unittest
from unittest.mock import MagicMock, patch

from application.core.models import Observation, Product
from application.rules.models import Rule
from application.rules.services.simulator import simulate_rule


class TestSimulateRule(unittest.TestCase):

    def setUp(self):
        # Create mock objects for testing
        self.mock_product = MagicMock(spec=Product)
        self.mock_product.name = "Test Product"
        self.mock_product.is_product_group = False

        self.mock_observation = MagicMock(spec=Observation)
        self.mock_observation.product = self.mock_product
        self.mock_observation.title = "Test Observation"

        self.mock_rule = MagicMock(spec=Rule)
        self.mock_rule.product = None
        self.mock_rule.parser = None
        self.mock_rule.scanner_prefix = None

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_with_product(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        mock_observation_manager.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = [
            self.mock_observation
        ]
        mock_check_rule.return_value = True

        # Set rule with product
        self.mock_rule.product = self.mock_product

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], self.mock_observation)

        # Verify mocks were called correctly
        mock_observation_manager.filter.assert_called_once_with(product=self.mock_product)
        mock_check_rule.assert_called_once()
        mock_get_products.assert_not_called()

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_with_product_group(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        self.mock_product_group = MagicMock(spec=Product)
        self.mock_product_group.name = "Test Product Group"
        self.mock_product_group.is_product_group = True

        self.mock_product.product_group = self.mock_product_group

        mock_observation_manager.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = [
            self.mock_observation
        ]
        mock_check_rule.return_value = True

        # Set rule with product
        self.mock_rule.product = self.mock_product_group

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], self.mock_observation)

        # Verify mocks were called correctly
        mock_observation_manager.filter.assert_called_once_with(product__in=self.mock_product_group.products.all())
        mock_check_rule.assert_called_once()
        mock_get_products.assert_not_called()

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_without_product(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        mock_observation_manager.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = [
            self.mock_observation
        ]
        mock_check_rule.return_value = True
        mock_get_products.return_value = [self.mock_product]

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], self.mock_observation)

        # Verify mocks were called correctly
        mock_observation_manager.filter.assert_called_once_with(
            product__in=[self.mock_product], product__apply_general_rules=True
        )
        mock_check_rule.assert_called_once()
        mock_get_products.assert_called_once()

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_with_parser(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        mock_observation_manager.filter.return_value.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = [
            self.mock_observation
        ]
        mock_check_rule.return_value = True
        mock_get_products.return_value = [self.mock_product]

        # Set rule with parser
        self.mock_rule.parser = "Test Parser"

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], self.mock_observation)

        # Verify mocks were called correctly
        mock_observation_manager.filter.assert_called_once_with(
            product__in=[self.mock_product], product__apply_general_rules=True
        )
        mock_observation_manager.filter().filter.assert_called_once_with(parser="Test Parser")
        mock_check_rule.assert_called_once()

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_with_scanner_prefix(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        mock_observation_manager.filter.return_value.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = [
            self.mock_observation
        ]
        mock_check_rule.return_value = True
        mock_get_products.return_value = [self.mock_product]

        # Set rule with scanner prefix
        self.mock_rule.scanner_prefix = "Test Scanner"

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result[1]), 1)
        self.assertEqual(result[1][0], self.mock_observation)

        # Verify mocks were called correctly
        mock_observation_manager.filter.assert_called_once_with(
            product__in=[self.mock_product], product__apply_general_rules=True
        )
        mock_observation_manager.filter().filter.assert_called_once_with(scanner__startswith="Test Scanner")
        mock_check_rule.assert_called_once()

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_no_matches(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        mock_observation_manager.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = [
            self.mock_observation
        ]
        mock_check_rule.return_value = False
        mock_get_products.return_value = [self.mock_product]

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 0)
        self.assertEqual(len(result[1]), 0)

        # Verify mocks were called correctly
        mock_check_rule.assert_called_once()

    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine.check_rule_for_observation")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_simulate_rule_max_observations(self, mock_observation_manager, mock_check_rule, mock_get_products):
        # Setup mocks
        observations = [MagicMock(spec=Observation) for _ in range(150)]
        for i, obs in enumerate(observations):
            obs.title = f"Observation {i}"

        mock_observation_manager.filter.return_value.order_by.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value.select_related.return_value = (
            observations
        )
        mock_check_rule.return_value = True
        mock_get_products.return_value = [self.mock_product]

        # Call the function
        result = simulate_rule(self.mock_rule)

        # Assertions
        self.assertEqual(result[0], 150)  # Total count
        self.assertEqual(len(result[1]), 100)  # Max should be 100

        # Verify that only first 100 observations were added
        for i, observation in enumerate(result[1]):
            self.assertEqual(observation.title, f"Observation {i}")

        # Verify mocks were called correctly
        mock_check_rule.assert_called()
        self.assertGreaterEqual(mock_check_rule.call_count, 100)
