from unittest.mock import call, patch

from application.core.models import Product
from application.rules.services.rule_engine import Rule_Engine, _check_regex
from unittests.base_test_case import BaseTestCase


class TestRuleEngine(BaseTestCase):
    def _rule_filter_conditionally(self, *args, **kwargs):
        if kwargs.get("product") == self.product_1:
            return [self.product_rule_1]
        elif kwargs.get("product__isnull") is True:
            return [self.general_rule]
        else:
            raise Exception("wrong parameters for _rule_filter_conditionally")

    # --- __init__ ---

    @patch("application.rules.models.Rule.objects.filter")
    def test_init_donot_apply_general_rules(self, mock_rule):
        mock_rule.return_value = [self.product_rule_1]

        self.product_1.apply_general_rules = False
        rule_engine = Rule_Engine(self.product_1)

        self.assertEqual(rule_engine.rules, [self.product_rule_1])
        mock_rule.assert_called_once()
        mock_rule.assert_called_with(
            product=self.product_1,
            enabled=True,
            approval_status__in=["Approved", "Auto approved"],
        )

    @patch("application.rules.models.Rule.objects.filter")
    def test_init_apply_general_rules(self, mock_rule):
        mock_rule.side_effect = self._rule_filter_conditionally

        self.product_1.apply_general_rules = True
        rule_engine = Rule_Engine(self.product_1)

        self.assertEqual(rule_engine.rules, [self.product_rule_1, self.general_rule])
        mock_rule.assert_has_calls(
            [
                call(
                    product=self.product_1,
                    enabled=True,
                    approval_status__in=["Approved", "Auto approved"],
                ),
                call(
                    product__isnull=True,
                    enabled=True,
                    approval_status__in=["Approved", "Auto approved"],
                ),
            ]
        )

    # --- apply_rules ---

    # --- _check_regex ---

    def test_check_regex_no_pattern(self):
        product = Product()
        product.save()
        rule_engine = Rule_Engine(product)
        self.assertTrue(_check_regex("", "value"))

    def test_check_regex_no_value(self):
        product = Product()
        product.save()
        rule_engine = Rule_Engine(product)
        self.assertFalse(_check_regex("pattern", ""))

    def test_check_regex_no_match(self):
        product = Product()
        product.save()
        rule_engine = Rule_Engine(product)
        self.assertFalse(_check_regex("pattern", "value"))

    def test_check_regex_match(self):
        product = Product()
        product.save()
        rule_engine = Rule_Engine(product)
        self.assertTrue(_check_regex("v.+lue", "VALUE"))
