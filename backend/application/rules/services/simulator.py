from copy import copy
from typing import Tuple

from application.core.models import Observation
from application.core.queries.product import get_products
from application.core.services.observation import normalize_observation_fields
from application.rules.models import Rule
from application.rules.services.rule_engine import Rule_Engine
from application.rules.types import Rule_Type

MAX_OBSERVATIONS = 100


def simulate_rule(rule: Rule) -> Tuple[int, list[Observation]]:
    number_observations = 0
    simulation_results: list[Observation] = []

    if rule.product:
        if rule.product.is_product_group:
            products = rule.product.products.all()
            observations = Observation.objects.filter(product__in=products)
        else:
            observations = Observation.objects.filter(product=rule.product)
    else:
        observations = Observation.objects.filter(product__in=get_products(), product__apply_general_rules=True)

    if rule.type == Rule_Type.RULE_TYPE_FIELDS:
        if rule.parser:
            observations = observations.filter(parser=rule.parser)
        if rule.scanner_prefix:
            observations = observations.filter(scanner__startswith=rule.scanner_prefix)

    observations = (
        observations.order_by("product__name", "title")
        .select_related("product")
        .select_related("product__product_group")
        .select_related("branch")
        .select_related("parser")
        .select_related("general_rule")
        .select_related("product_rule")
    )

    rule_engines: dict[int, Rule_Engine] = {}

    for observation in observations:
        rule_engine = rule_engines.get(observation.product.pk)
        if not rule_engine:
            rule_engine = Rule_Engine(observation.product)
            rule_engines[observation.product.pk] = rule_engine

        observation_before = copy(observation)

        observation_before.rule_status = ""
        observation_before.rule_rego_status = ""
        observation_before.rule_severity = ""
        observation_before.rule_rego_status = ""
        observation_before.rule_priority = None
        observation_before.rule_rego_priority = None
        observation_before.rule_vex_justification = ""
        observation_before.rule_rego_vex_justification = ""
        observation_before.general_rule = None
        observation_before.general_rule_rego = None
        observation_before.product_rule = None
        observation_before.product_rule_rego = None

        normalize_observation_fields(observation)

        if rule_engine.check_rule_for_observation(rule, observation, observation_before, True):
            number_observations += 1
            if len(simulation_results) < MAX_OBSERVATIONS:
                simulation_results.append(observation)

    return number_observations, simulation_results
