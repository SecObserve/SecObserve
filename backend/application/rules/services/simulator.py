from django.core.paginator import Paginator
from django.db.models import QuerySet

from application.core.models import Observation
from application.core.queries.product import get_products
from application.rules.models import Rule
from application.rules.services.rule_engine import Rule_Engine

MAX_OBSERVATIONS = 100


def simulate_rule(rule: Rule) -> list[Observation]:
    simulation_results: list[Observation] = []

    observations = _get_observations(rule)

    rule_engines: dict[int, Rule_Engine] = {}

    paginator = Paginator(observations, 1000)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        for observation in page.object_list:
            rule_engine = rule_engines.get(observation.product.pk)
            if not rule_engine:
                rule_engine = Rule_Engine(observation.product)
                rule_engines[observation.product.pk] = rule_engine

            if rule_engine.check_rule_for_observation(rule, observation, None, True):
                if len(simulation_results) < MAX_OBSERVATIONS:
                    simulation_results.append(observation)
                if len(simulation_results) == MAX_OBSERVATIONS:
                    break
        else:  # see https://stackoverflow.com/questions/189645/how-can-i-break-out-of-multiple-loops
            continue
        break

    return simulation_results


def _get_observations(rule: Rule) -> QuerySet:
    if rule.product:
        if rule.product.is_product_group:
            products = rule.product.products.all()
            observations = Observation.objects.filter(product__in=products)
        else:
            observations = Observation.objects.filter(product=rule.product)
    else:
        observations = Observation.objects.filter(product__in=get_products(), product__apply_general_rules=True)

    if rule.parser:
        observations = observations.filter(parser=rule.parser)
    if rule.scanner_prefix:
        observations = observations.filter(scanner__startswith=rule.scanner_prefix)

    observations = (
        observations.order_by("product__name", "title")
        .select_related("product")
        .select_related("product__product_group")
        .select_related("branch")
        .select_related("origin_service")
        .select_related("parser")
        .select_related("general_rule")
        .select_related("product_rule")
    )
    return observations
