import unittest
from unittest.mock import MagicMock, patch

from application.core.models import Observation, Product
from application.rules.models import Rule
from application.rules.services.simulator import MAX_OBSERVATIONS, simulate_rule
from application.rules.types import Rule_Type


class TestSimulateRule(unittest.TestCase):

    def setUp(self):
        self.mock_product = MagicMock(spec=Product)
        self.mock_product.name = "Test Product"
        self.mock_product.is_product_group = False
        self.mock_product.pk = 1

        self.mock_observation = MagicMock(spec=Observation)
        self.mock_observation.product = self.mock_product
        self.mock_observation.title = "Test Observation"

        self.mock_rule = MagicMock(spec=Rule)
        self.mock_rule.product = None
        self.mock_rule.type = Rule_Type.RULE_TYPE_FIELDS
        self.mock_rule.parser = None
        self.mock_rule.scanner_prefix = None

    def _setup_queryset_mock(self, mock_obs_manager, observations):
        """Configure the chained queryset mock to return the given observations."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.__iter__ = lambda self_qs: iter(observations)
        mock_obs_manager.filter.return_value = mock_qs
        return mock_qs

    # --- Product routing tests ---

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_product_single(self, mock_obs_manager, mock_rule_engine_cls, mock_normalize):
        self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.product = self.mock_product

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        self.assertEqual(results, [self.mock_observation])
        mock_obs_manager.filter.assert_called_once_with(product=self.mock_product)

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_product_group(self, mock_obs_manager, mock_rule_engine_cls, mock_normalize):
        mock_product_group = MagicMock(spec=Product)
        mock_product_group.is_product_group = True
        self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.product = mock_product_group

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        self.assertEqual(results, [self.mock_observation])
        mock_obs_manager.filter.assert_called_once_with(
            product__in=mock_product_group.products.all()
        )

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_no_product_general_rule(
        self, mock_obs_manager, mock_rule_engine_cls, mock_get_products, mock_normalize
    ):
        mock_get_products.return_value = [self.mock_product]
        self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        self.assertEqual(results, [self.mock_observation])
        mock_obs_manager.filter.assert_called_once_with(
            product__in=[self.mock_product], product__apply_general_rules=True
        )
        mock_get_products.assert_called_once()

    # --- RULE_TYPE_FIELDS filtering tests ---

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_fields_type_with_parser_filter(
        self, mock_obs_manager, mock_rule_engine_cls, mock_get_products, mock_normalize
    ):
        mock_get_products.return_value = [self.mock_product]
        mock_qs = self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.parser = MagicMock()

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        mock_qs.filter.assert_any_call(parser=self.mock_rule.parser)

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_fields_type_with_scanner_prefix_filter(
        self, mock_obs_manager, mock_rule_engine_cls, mock_get_products, mock_normalize
    ):
        mock_get_products.return_value = [self.mock_product]
        mock_qs = self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.scanner_prefix = "Scanner/"

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        mock_qs.filter.assert_any_call(scanner__startswith="Scanner/")

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_fields_type_with_parser_and_scanner_prefix(
        self, mock_obs_manager, mock_rule_engine_cls, mock_get_products, mock_normalize
    ):
        mock_get_products.return_value = [self.mock_product]
        mock_qs = self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.parser = MagicMock()
        self.mock_rule.scanner_prefix = "Scanner/"

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        mock_qs.filter.assert_any_call(parser=self.mock_rule.parser)
        mock_qs.filter.assert_any_call(scanner__startswith="Scanner/")

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.get_products")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_rego_type_no_parser_or_scanner_filter(
        self, mock_obs_manager, mock_rule_engine_cls, mock_get_products, mock_normalize
    ):
        mock_get_products.return_value = [self.mock_product]
        mock_qs = self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.type = Rule_Type.RULE_TYPE_REGO
        self.mock_rule.parser = MagicMock()
        self.mock_rule.scanner_prefix = "Scanner/"

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 1)
        mock_qs.filter.assert_not_called()

    # --- Observation matching and counting tests ---

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_no_matches(self, mock_obs_manager, mock_rule_engine_cls, mock_normalize):
        self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = False
        self.mock_rule.product = self.mock_product

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 0)
        self.assertEqual(results, [])

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_empty_observations(self, mock_obs_manager, mock_rule_engine_cls, mock_normalize):
        self._setup_queryset_mock(mock_obs_manager, [])
        self.mock_rule.product = self.mock_product

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 0)
        self.assertEqual(results, [])
        mock_rule_engine_cls.assert_not_called()
        mock_normalize.assert_not_called()

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_max_observations_caps_results(self, mock_obs_manager, mock_rule_engine_cls, mock_normalize):
        observations = []
        for i in range(150):
            obs = MagicMock(spec=Observation)
            obs.product = self.mock_product
            obs.title = f"Observation {i}"
            observations.append(obs)

        self._setup_queryset_mock(mock_obs_manager, observations)
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.product = self.mock_product

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 150)
        self.assertEqual(len(results), MAX_OBSERVATIONS)
        for i in range(MAX_OBSERVATIONS):
            self.assertEqual(results[i].title, f"Observation {i}")

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_multiple_observations_mixed_matches(
        self, mock_obs_manager, mock_rule_engine_cls, mock_normalize
    ):
        obs_match = MagicMock(spec=Observation)
        obs_match.product = self.mock_product
        obs_no_match = MagicMock(spec=Observation)
        obs_no_match.product = self.mock_product

        self._setup_queryset_mock(mock_obs_manager, [obs_match, obs_no_match, obs_match])
        mock_engine = mock_rule_engine_cls.return_value
        mock_engine.check_rule_for_observation.side_effect = [True, False, True]
        self.mock_rule.product = self.mock_product

        count, results = simulate_rule(self.mock_rule)

        self.assertEqual(count, 2)
        self.assertEqual(results, [obs_match, obs_match])

    # --- Rule engine caching tests ---

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_rule_engine_cached_per_product(
        self, mock_obs_manager, mock_rule_engine_cls, mock_normalize
    ):
        product_a = MagicMock(spec=Product)
        product_a.pk = 10
        product_b = MagicMock(spec=Product)
        product_b.pk = 20

        obs_a1 = MagicMock(spec=Observation)
        obs_a1.product = product_a
        obs_a2 = MagicMock(spec=Observation)
        obs_a2.product = product_a
        obs_b = MagicMock(spec=Observation)
        obs_b.product = product_b

        self._setup_queryset_mock(mock_obs_manager, [obs_a1, obs_a2, obs_b])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = True
        self.mock_rule.product = self.mock_product

        simulate_rule(self.mock_rule)

        self.assertEqual(mock_rule_engine_cls.call_count, 2)
        mock_rule_engine_cls.assert_any_call(product_a)
        mock_rule_engine_cls.assert_any_call(product_b)

    # --- observation_before reset and normalize tests ---

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_normalize_called_for_each_observation(
        self, mock_obs_manager, mock_rule_engine_cls, mock_normalize
    ):
        obs1 = MagicMock(spec=Observation)
        obs1.product = self.mock_product
        obs2 = MagicMock(spec=Observation)
        obs2.product = self.mock_product

        self._setup_queryset_mock(mock_obs_manager, [obs1, obs2])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = False
        self.mock_rule.product = self.mock_product

        simulate_rule(self.mock_rule)

        self.assertEqual(mock_normalize.call_count, 2)

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.copy")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_observation_before_fields_are_reset(
        self, mock_obs_manager, mock_rule_engine_cls, mock_copy, mock_normalize
    ):
        obs_before = MagicMock(spec=Observation)
        mock_copy.return_value = obs_before

        self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_rule_engine_cls.return_value.check_rule_for_observation.return_value = False
        self.mock_rule.product = self.mock_product

        simulate_rule(self.mock_rule)

        self.assertEqual(obs_before.rule_status, "")
        self.assertEqual(obs_before.rule_rego_status, "")
        self.assertEqual(obs_before.rule_severity, "")
        self.assertIsNone(obs_before.rule_priority)
        self.assertIsNone(obs_before.rule_rego_priority)
        self.assertEqual(obs_before.rule_vex_justification, "")
        self.assertEqual(obs_before.rule_rego_vex_justification, "")
        self.assertIsNone(obs_before.general_rule)
        self.assertIsNone(obs_before.general_rule_rego)
        self.assertIsNone(obs_before.product_rule)
        self.assertIsNone(obs_before.product_rule_rego)
        mock_normalize.assert_called_once_with(obs_before)

    # --- check_rule_for_observation call tests ---

    @patch("application.rules.services.simulator.normalize_observation_fields")
    @patch("application.rules.services.simulator.Rule_Engine")
    @patch("application.rules.services.simulator.Observation.objects")
    def test_check_rule_called_with_simulation_true(
        self, mock_obs_manager, mock_rule_engine_cls, mock_normalize
    ):
        self._setup_queryset_mock(mock_obs_manager, [self.mock_observation])
        mock_engine = mock_rule_engine_cls.return_value
        mock_engine.check_rule_for_observation.return_value = True
        self.mock_rule.product = self.mock_product

        simulate_rule(self.mock_rule)

        args, kwargs = mock_engine.check_rule_for_observation.call_args
        self.assertEqual(args[0], self.mock_rule)
        self.assertEqual(args[1], self.mock_observation)
        self.assertTrue(args[3])
