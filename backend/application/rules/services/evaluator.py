from dataclasses import dataclass
from itertools import batched

from django.db.models import Q
from django.dispatch import Signal

from application.core.models import Observation, Product
from application.core.services.security_gate import check_security_gate
from application.rules.models import Rule
from application.rules.services.rule_engine import Rule_Engine

CHUNK_SIZE = 1000

# Requests a background evaluation of a general rule. The receiver lives in
# application.background_tasks, which is a higher layer and must not be imported from here.
general_rule_evaluation_requested = Signal()


def request_general_rule_evaluation(rule_id: int) -> None:
    general_rule_evaluation_requested.send(sender=Rule, rule_id=rule_id)


@dataclass
class EvaluationResult:
    observations_processed: int
    observations_changed: int


def evaluate_general_rule(rule: Rule) -> EvaluationResult:
    """
    Applies a general rule to all observations of products with apply_general_rules
    enabled and reverts stale effects. A disabled or unapproved rule is revert-only.
    """
    pks = _get_affected_observation_pks(rule)

    rule_engines: dict[int, Rule_Engine] = {}
    products_with_changes: dict[int, Product] = {}
    observations_processed = 0
    observations_changed = 0

    for chunk in batched(pks, CHUNK_SIZE):
        # Chunked by the initial primary keys: the rule engine saves changed observations,
        # which would move them out of offset-paginated pages.
        observations = (
            Observation.objects.filter(pk__in=chunk)
            .select_related("product")
            .select_related("product__product_group")
            .select_related("branch")
            .select_related("origin_service")
            .select_related("parser")
            .select_related("general_rule")
            .select_related("product_rule")
            .select_related("general_rule_rego")
            .select_related("product_rule_rego")
        )
        for observation in observations:
            rule_engine = rule_engines.get(observation.product.pk)
            if not rule_engine:
                rule_engine = Rule_Engine(observation.product)
                rule_engines[observation.product.pk] = rule_engine

            snapshot_before = _snapshot(observation)
            rule_engine.apply_rules_for_observation(observation)

            observations_processed += 1
            if _snapshot(observation) != snapshot_before:
                observations_changed += 1
                products_with_changes[observation.product.pk] = observation.product

    for product in products_with_changes.values():
        check_security_gate(product)

    return EvaluationResult(
        observations_processed=observations_processed,
        observations_changed=observations_changed,
    )


def _get_affected_observation_pks(rule: Rule) -> list[int]:
    # No user-based product filtering: no current user exists in a background task.
    scope = Q(product__apply_general_rules=True)
    if rule.parser:
        scope &= Q(parser=rule.parser)
    if rule.scanner_prefix:
        scope &= Q(scanner__startswith=rule.scanner_prefix)

    # Linked observations are not narrowed by the scope, so stale effects are reverted
    # even after the rule's matchers, its type or a product's flag have been changed.
    linked = Q(general_rule=rule) | Q(general_rule_rego=rule)

    return list(Observation.objects.filter(scope | linked).values_list("pk", flat=True))


def _snapshot(observation: Observation) -> tuple:
    """All observation fields the rule engine pass can change, to detect changes."""
    return (
        observation.general_rule_id,
        observation.product_rule_id,
        observation.general_rule_rego_id,
        observation.product_rule_rego_id,
        observation.rule_severity,
        observation.rule_status,
        observation.rule_priority,
        observation.rule_vex_justification,
        observation.rule_vex_remediations,
        observation.rule_rego_severity,
        observation.rule_rego_status,
        observation.rule_rego_priority,
        observation.rule_rego_vex_justification,
        observation.rule_rego_vex_remediations,
        observation.current_severity,
        observation.current_status,
        observation.current_priority,
        observation.current_vex_justification,
        observation.current_vex_remediations,
        observation.risk_acceptance_expiry_date,
    )
