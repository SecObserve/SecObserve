from copy import copy
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

import jsonpickle
from django.core.management import call_command

from application.core.models import Evidence, Observation, Product, Reference
from application.core.types import Status
from application.rules.models import Rule
from application.rules.services.rule_engine import Rule_Engine, _check_regex
from application.rules.types import Rule_Type
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
        )

    @patch("application.rules.services.rule_engine.Settings")
    @patch("application.rules.models.Rule.objects.filter")
    def test_init_apply_general_rules(self, mock_rule, mock_settings):
        mock_rule.side_effect = self._rule_filter_conditionally
        mock_settings.load.return_value.feature_general_rules_need_approval = False

        self.product_1.apply_general_rules = True
        rule_engine = Rule_Engine(self.product_1)

        self.assertEqual(rule_engine.rules, [self.product_rule_1, self.general_rule])
        mock_rule.assert_has_calls(
            [
                call(
                    product=self.product_1,
                    enabled=True,
                ),
                call(
                    product__isnull=True,
                    enabled=True,
                ),
            ]
        )

    @patch("application.rules.models.Rule.objects.filter")
    def test_init_product_rules_need_approval(self, mock_rule):
        product_qs = MagicMock()
        product_qs.filter.return_value = [self.product_rule_1]
        mock_rule.return_value = product_qs

        self.product_1.apply_general_rules = False
        self.product_1.product_rules_need_approval = True
        rule_engine = Rule_Engine(self.product_1)

        self.assertEqual(rule_engine.rules, [self.product_rule_1])
        mock_rule.assert_called_once_with(product=self.product_1, enabled=True)
        product_qs.filter.assert_called_once_with(approval_status__in=["Approved", "Auto approved"])

    @patch("application.rules.services.rule_engine.Settings")
    @patch("application.rules.models.Rule.objects.filter")
    def test_init_general_rules_need_approval(self, mock_rule, mock_settings):
        general_qs = MagicMock()
        general_qs.filter.return_value = [self.general_rule]

        def _filter(*args, **kwargs):
            if kwargs.get("product") == self.product_1:
                return [self.product_rule_1]
            elif kwargs.get("product__isnull") is True:
                return general_qs
            else:
                raise Exception("wrong parameters for _filter")

        mock_rule.side_effect = _filter
        mock_settings.load.return_value.feature_general_rules_need_approval = True

        self.product_1.apply_general_rules = True
        rule_engine = Rule_Engine(self.product_1)

        self.assertEqual(rule_engine.rules, [self.product_rule_1, self.general_rule])
        mock_rule.assert_has_calls(
            [
                call(product=self.product_1, enabled=True),
                call(product__isnull=True, enabled=True),
            ]
        )
        general_qs.filter.assert_called_once_with(approval_status__in=["Approved", "Auto approved"])

    @patch("application.rules.models.Rule.objects.filter")
    def test_init_product_group_rules_need_approval(self, mock_rule):
        group_rule = Rule(name="group_rule", product=self.product_group_1)
        product_qs = MagicMock()
        product_qs.filter.return_value = [self.product_rule_1]
        group_qs = MagicMock()
        group_qs.filter.return_value = [group_rule]

        def _filter(*args, **kwargs):
            if kwargs.get("product") == self.product_1:
                return product_qs
            elif kwargs.get("product") == self.product_group_1:
                return group_qs
            else:
                raise Exception("wrong parameters for _filter")

        mock_rule.side_effect = _filter

        self.product_1.apply_general_rules = False
        self.product_1.product_group = self.product_group_1
        self.product_group_1.product_rules_need_approval = True
        rule_engine = Rule_Engine(self.product_1)

        self.assertEqual(rule_engine.rules, [self.product_rule_1, group_rule])
        mock_rule.assert_has_calls(
            [
                call(product=self.product_1, enabled=True),
                call(product=self.product_group_1, enabled=True),
            ]
        )
        product_qs.filter.assert_called_once_with(approval_status__in=["Approved", "Auto approved"])
        group_qs.filter.assert_called_once_with(approval_status__in=["Approved", "Auto approved"])

    @patch("application.rules.services.rule_engine.jsonpickle.dumps", return_value="{}")
    @patch("application.rules.services.rule_engine.RegoInterpreter")
    @patch("application.rules.models.Rule.objects.filter")
    def test_check_rule_rego_lazy_loads_interpreter(self, mock_rule, mock_rego_interpreter, _mock_dumps):
        mock_rule.return_value = []
        mock_rego_interpreter.return_value.query.return_value = {"severity": "High"}
        rule_engine = Rule_Engine(self.product_1)
        rule = Rule(
            id=1,
            name="rego_rule",
            type=Rule_Type.RULE_TYPE_REGO,
            rego_module="package rule",
        )
        observation = Observation(title="observation", product=self.product_1)
        observation_before = MagicMock(spec=Observation)
        jsonpickle_output_before = jsonpickle.dumps({"b": 1, "a": 2}, unpicklable=False)

        result = rule_engine.check_rule_for_observation(rule, observation, observation_before, True)

        self.assertTrue(result)
        mock_rego_interpreter.assert_called_once_with("package rule")
        mock_rego_interpreter.return_value.query.assert_called_once_with({"product_name": "product_1"})
        self.assertEqual(rule_engine.rego_interpreters[rule.pk], mock_rego_interpreter.return_value)
        self.assertEqual(jsonpickle_output_before, jsonpickle.dumps({"b": 1, "a": 2}, unpicklable=False))

    def _check_rego_risk_accepted(self, mock_rego_interpreter, status_before: str) -> Observation:
        mock_rego_interpreter.return_value.query.return_value = {"status": Status.STATUS_RISK_ACCEPTED}
        rule_engine = Rule_Engine(self.product_1)
        rule = Rule(id=1, name="rego_rule", type=Rule_Type.RULE_TYPE_REGO, rego_module="package rule")
        observation = Observation(
            title="observation",
            product=self.product_1,
            current_status=status_before,
            risk_acceptance_expiry_date=date(2026, 1, 1),
        )
        observation_before = copy(observation)

        self.assertTrue(rule_engine._check_rule_rego(rule, observation, observation_before))
        return observation

    @patch(
        "application.rules.services.rule_engine.calculate_risk_acceptance_expiry_date", return_value=date(2027, 6, 30)
    )
    @patch("application.rules.services.rule_engine.jsonpickle.dumps", return_value="{}")
    @patch("application.rules.services.rule_engine.RegoInterpreter")
    @patch("application.rules.models.Rule.objects.filter")
    def test_check_rule_rego_risk_accepted_sets_expiry_date(self, mock_rule, mock_rego_interpreter, *_mocks):
        mock_rule.return_value = []

        observation = self._check_rego_risk_accepted(mock_rego_interpreter, Status.STATUS_OPEN)

        self.assertEqual(Status.STATUS_RISK_ACCEPTED, observation.current_status)
        self.assertEqual(date(2027, 6, 30), observation.risk_acceptance_expiry_date)

    @patch(
        "application.rules.services.rule_engine.calculate_risk_acceptance_expiry_date", return_value=date(2027, 6, 30)
    )
    @patch("application.rules.services.rule_engine.jsonpickle.dumps", return_value="{}")
    @patch("application.rules.services.rule_engine.RegoInterpreter")
    @patch("application.rules.models.Rule.objects.filter")
    def test_check_rule_rego_already_risk_accepted_keeps_expiry_date(self, mock_rule, mock_rego_interpreter, *_mocks):
        mock_rule.return_value = []

        observation = self._check_rego_risk_accepted(mock_rego_interpreter, Status.STATUS_RISK_ACCEPTED)

        self.assertEqual(date(2026, 1, 1), observation.risk_acceptance_expiry_date)

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


class TestRuleEngineRegoInput(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    @patch("application.rules.services.rule_engine.RegoInterpreter")
    @patch("application.rules.models.Rule.objects.filter")
    def test_check_rule_rego_input_only_database_fields(self, mock_rule, mock_rego_interpreter):
        mock_rule.return_value = []
        mock_rego_interpreter.return_value.query.return_value = {}

        Reference.objects.create(observation_id=1, url="https://example.com/reference")
        Evidence.objects.create(observation_id=1, name="evidence", evidence='{"finding": "raw scanner data"}')
        observation = Observation.objects.prefetch_related("references", "evidences").get(id=1)
        self.assertIn("references", observation._prefetched_objects_cache)
        self.assertIn("evidences", observation._prefetched_objects_cache)
        self.assertTrue(observation.references.all())
        self.assertTrue(observation.evidences.all())
        observation.cvss3_score = Decimal("9.8")
        # Set by the parsers, not a database field
        observation.unsaved_references = ["https://example.com/unsaved"]

        rule = Rule(
            id=1,
            name="rego_rule",
            type=Rule_Type.RULE_TYPE_REGO,
            rego_module="package rule",
        )
        rule_engine = Rule_Engine(observation.product)

        rule_engine.check_rule_for_observation(rule, observation, None, True)

        mock_rego_interpreter.return_value.query.assert_called_once()
        rego_input = mock_rego_interpreter.return_value.query.call_args.args[0]

        expected_keys = {
            field.attname
            for field in Observation._meta.concrete_fields
            if getattr(observation, field.attname) is not None and getattr(observation, field.attname) != ""
        }
        expected_keys.update(["product_name", "branch_name"])
        if observation.origin_service:
            expected_keys.add("origin_service_name")
        self.assertEqual(expected_keys, set(rego_input.keys()))

        self.assertEqual("db_observation_internal", rego_input["title"])
        self.assertEqual(observation.product_id, rego_input["product_id"])
        self.assertEqual(9.8, rego_input["cvss3_score"])
        self.assertEqual(observation.product.name, rego_input["product_name"])
        self.assertEqual(observation.branch.name, rego_input["branch_name"])
        for key in ["_state", "_prefetched_objects_cache", "unsaved_references", "references", "evidences"]:
            self.assertNotIn(key, rego_input)
