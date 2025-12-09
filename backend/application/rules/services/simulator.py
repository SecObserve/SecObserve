from typing import Tuple

from application.core.models import Observation
from application.core.queries.product import get_products
from application.rules.models import Rule
from application.rules.services.rule_engine import check_rule_for_observation

MAX_OBSERVATIONS = 100


def simulate_rule(rule: Rule) -> Tuple[int, list[Observation]]:
    number_observations = 0
    simulation_results: list[Observation] = []

    if rule.product:
        observations = Observation.objects.filter(product=rule.product)
    else:
        observations = Observation.objects.filter(product__in=get_products(), product__apply_general_rules=True)

    if rule.parser:
        observations = observations.filter(parser=rule.parser)
    if rule.scanner_prefix:
        observations = observations.filter(scanner__startswith=rule.scanner_prefix)

    observations = observations.order_by("product__name", "title")

    for observation in observations:
        previous_product_rule = observation.product_rule if observation.product_rule else None
        previous_general_rule = observation.general_rule if observation.general_rule else None

        if check_rule_for_observation(rule, observation, previous_general_rule, previous_product_rule, True):
            number_observations += 1
            if len(simulation_results) < MAX_OBSERVATIONS:
                simulation_results.append(observation)

    return number_observations, simulation_results
