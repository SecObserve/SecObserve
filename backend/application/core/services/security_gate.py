import logging
from dataclasses import dataclass
from decimal import Decimal
from functools import reduce
from itertools import batched
from operator import and_, or_
from typing import Any, Mapping, Optional, Union

from django.db.models import Q, QuerySet

from application.commons.models import Settings
from application.commons.services.security_gate_conditions import (
    SECURITY_GATE_ADVANCED_FIELDS,
    conditions_have_a_rule,
    normalize_security_gate_conditions,
)
from application.core.models import Branch, Observation, Product
from application.core.queries.observation import (
    count_active_observations_by_product_and_severity,
    count_active_observations_by_severity,
)
from application.core.queries.product import (
    get_product_by_id,
    populate_product_count_annotations,
)
from application.core.types import Security_Gate_Operator, Severity
from application.notifications.services.send_notifications_security_gate import (
    send_product_security_gate_notification,
)
from application.notifications.services.tasks import handle_task_exception

logger = logging.getLogger("secobserve.core")

SEVERITIES = ("critical", "high", "medium", "low", "none", "unknown")
SECURITY_GATES_BATCH_SIZE = 1000
# Thresholds are keyed by the lower case severity, observations carry the title case one.
SEVERITY_TITLES = {
    "critical": Severity.SEVERITY_CRITICAL,
    "high": Severity.SEVERITY_HIGH,
    "medium": Severity.SEVERITY_MEDIUM,
    "low": Severity.SEVERITY_LOW,
    "none": Severity.SEVERITY_NONE,
    "unknown": Severity.SEVERITY_UNKNOWN,
}
SECURITY_GATE_FIELDS = (
    ("security_gate_active",)
    + tuple(f"security_gate_threshold_{severity}" for severity in SEVERITIES)
    + SECURITY_GATE_ADVANCED_FIELDS
)
# The observations of the products that use the instance-wide gate, neither their own nor their group's
SETTINGS_GATE_OBSERVATIONS = Q(product__security_gate_active__isnull=True) & (
    Q(product__product_group__isnull=True) | Q(product__product_group__security_gate_active__isnull=True)
)


@dataclass(frozen=True)
class Security_Gate_Rule:
    operator: str
    known_exploited: bool
    exploit_tooling: bool
    proof_of_concept: bool
    epss_min: Optional[Decimal]
    network_vector: bool
    fix_available: bool


# One rule list per title case severity, an empty list means that every observation counts.
RulesBySeverity = dict[str, list[Security_Gate_Rule]]


def check_security_gate(product: Product, settings: Optional[Settings] = None) -> None:
    if product.is_product_group:
        raise ValueError(f"{product.name} is a product group")

    new_security_gate_passed = None

    thresholds = get_security_gate_thresholds(product, settings)
    if thresholds is not None:
        rules = get_security_gate_rules(product, settings)
        if rules is None:
            annotated_product = get_product_by_id(
                product_id=product.pk, is_product_group=False, with_observation_annotations=True
            )
            if not annotated_product:
                raise ValueError(f"Product {product.pk} not found while calculating security gate.")

            new_security_gate_passed = evaluate_security_gate(annotated_product, thresholds)
        else:
            new_security_gate_passed = evaluate_security_gate(product, thresholds, rules)

    _update_security_gate(product, new_security_gate_passed)


def check_security_gates(products: QuerySet[Product]) -> None:
    # Many products at once, e.g. when the thresholds they inherit have changed: the observations are counted for a
    # batch of products in one query, without the license counts that check_security_gate() loads as well.
    settings = Settings.load()
    for batch in batched(products.select_related("product_group"), SECURITY_GATES_BATCH_SIZE):
        gates_of_products = [
            (product, get_security_gate_thresholds(product, settings), get_security_gate_rules(product, settings))
            for product in batch
        ]
        # A gate with rules counts its observations in a query of its own
        populate_product_count_annotations(
            [product for product, thresholds, rules in gates_of_products if thresholds is not None and rules is None],
            is_product_group=False,
        )
        for product, thresholds, rules in gates_of_products:
            security_gate_passed = (
                evaluate_security_gate(product, thresholds, rules) if thresholds is not None else None
            )
            _update_security_gate(product, security_gate_passed)


def check_security_gates_with_conditions() -> tuple[int, int]:
    """
    Rechecks every product whose gate uses rules, because EPSS scores and exploit flags change without an import.
    Returns how many gates were checked and for how many products the check failed.
    """
    settings = Settings.load()
    checked = 0
    failed = 0
    for product in Product.objects.filter(is_product_group=False).select_related("product_group"):
        if get_security_gate_rules(product, settings) is None:
            continue
        try:
            check_security_gate(product, settings)
            checked += 1
        except Exception as e:
            failed += 1
            logger.exception("Security gate recheck - %s: failed with exception", product)
            handle_task_exception(e, product=product)
    return checked, failed


def _update_security_gate(product: Product, new_security_gate_passed: Optional[bool]) -> None:
    if product.security_gate_passed != new_security_gate_passed:
        product.security_gate_passed = new_security_gate_passed
        product.save()
        send_product_security_gate_notification(product)


def check_security_gate_observation(observation: Observation) -> None:
    if observation.branch == observation.product.repository_default_branch:
        check_security_gate(observation.product)


def _get_security_gate_source(
    product: Product, settings: Optional[Settings] = None
) -> Optional[Union[Product, Settings]]:
    # Returns the object whose security gate fields apply, None if no security gate is to be applied
    product_group = product.product_group

    security_gate_active: Optional[bool]
    if product_group and product_group.security_gate_active is not None:
        security_gate_active = product_group.security_gate_active
    else:
        security_gate_active = product.security_gate_active

    if security_gate_active is False:
        return None

    if security_gate_active is True:
        return product_group if product_group and product_group.security_gate_active is True else product

    settings = settings or Settings.load()
    if not settings.security_gate_active:
        return None

    return settings


def get_security_gate_thresholds(product: Product, settings: Optional[Settings] = None) -> Optional[dict[str, int]]:
    source = _get_security_gate_source(product, settings)
    if source is None:
        return None

    if isinstance(source, Settings):
        return {severity: getattr(source, f"security_gate_threshold_{severity}") for severity in SEVERITIES}

    return {severity: getattr(source, f"security_gate_threshold_{severity}") or 0 for severity in SEVERITIES}


def resolve_security_gate_rules(conditions: Any) -> RulesBySeverity:
    """The effective rules per severity: its own list when overridden, else the default set."""
    normalized = normalize_security_gate_conditions(conditions)
    default = [_rule_from_dict(rule) for rule in normalized["default"]]

    rules: RulesBySeverity = {}
    for severity in SEVERITY_TITLES.values():
        if severity in normalized["severities"]:
            rules[severity] = [_rule_from_dict(rule) for rule in normalized["severities"][severity]]
        else:
            rules[severity] = default
    return rules


def get_security_gate_rules(product: Product, settings: Optional[Settings] = None) -> Optional[RulesBySeverity]:
    # Returns None if the gate counts every observation, as without the advanced mode
    source = _get_security_gate_source(product, settings)
    if source is None or source.security_gate_advanced is not True:
        return None

    normalized = normalize_security_gate_conditions(source.security_gate_conditions or {})
    if not conditions_have_a_rule(normalized):
        return None

    return resolve_security_gate_rules(normalized)


def get_security_gate_condition_filter(rules: RulesBySeverity) -> Q:
    """
    Observations that count for the gate: every observation of a severity without rules, and of
    a severity with rules every observation without a CVE plus the CVEs matching one of its rules.
    """
    cve = Q(vulnerability_id__startswith="CVE-")

    unconditioned = [severity for severity, severity_rules in rules.items() if not severity_rules]
    clauses = []
    for severity, severity_rules in rules.items():
        if severity_rules:
            matched = reduce(or_, (_rule_filter(rule) for rule in severity_rules))
            clauses.append(Q(current_severity=severity) & (~cve | (cve & matched)))

    if unconditioned:
        clauses.insert(0, Q(current_severity__in=unconditioned))
    return reduce(or_, clauses)


def _rule_filter(rule: Security_Gate_Rule) -> Q:
    parts = []
    if rule.known_exploited:
        parts.append(Q(cve_found_in__icontains="CISA KEV") | Q(cve_found_in__icontains="VulnCheck KEV"))
    if rule.exploit_tooling:
        parts.append(
            Q(cve_found_in__icontains="Metasploit")
            | Q(cve_found_in__icontains="Nuclei")
            | Q(cve_found_in__icontains="Exploit-DB")
        )
    if rule.proof_of_concept:
        parts.append(Q(cve_found_in__icontains="PoC GitHub"))
    if rule.epss_min is not None:
        parts.append(Q(epss_score__gte=rule.epss_min))
    if rule.network_vector:
        parts.append(_network_vector_filter("cvss3_vector") | _network_vector_filter("cvss4_vector"))
    if rule.fix_available:
        parts.append(Q(fix_available=True))

    return reduce(and_ if rule.operator == Security_Gate_Operator.OPERATOR_ALL else or_, parts)


def _network_vector_filter(field: str) -> Q:
    return (
        Q(**{f"{field}__contains": "/AV:N/"})
        & Q(**{f"{field}__contains": "/PR:N/"})
        & Q(**{f"{field}__contains": "/UI:N/"})
    )


def _rule_from_dict(rule: Mapping[str, Any]) -> Security_Gate_Rule:
    epss_min = rule["epss_min"]
    return Security_Gate_Rule(
        operator=rule["operator"],
        known_exploited=rule["known_exploited"],
        exploit_tooling=rule["exploit_tooling"],
        proof_of_concept=rule["proof_of_concept"],
        epss_min=Decimal(str(epss_min)) if epss_min is not None else None,
        network_vector=rule["network_vector"],
        fix_available=rule["fix_available"],
    )


def get_security_gate_observation_counts(
    counted: Union[Product, Branch], rules: Optional[RulesBySeverity]
) -> dict[str, int]:
    """Active observations per lower case severity: from the annotations without rules, else counted under the rules."""
    if rules is None:
        counts = {}
        for severity in SEVERITIES:
            count = getattr(counted, f"active_{severity}_observation_count", None)
            if count is None:
                raise ValueError("Observation counts are None.")
            counts[severity] = count
        return counts

    if isinstance(counted, Branch):
        counted_by_title = count_active_observations_by_severity(
            counted.product, counted, get_security_gate_condition_filter(rules)
        )
    else:
        counted_by_title = count_active_observations_by_severity(
            counted, None, get_security_gate_condition_filter(rules)
        )
    return {severity: counted_by_title[title] for severity, title in SEVERITY_TITLES.items()}


def evaluate_security_gate(
    counted: Union[Product, Branch], thresholds: dict[str, int], rules: Optional[RulesBySeverity] = None
) -> bool:
    # Without rules counted needs to be annotated with the active observation counts per severity
    counts = get_security_gate_observation_counts(counted, rules)
    for severity, threshold in thresholds.items():
        if counts[severity] > threshold:
            return False

    return True


def preview_security_gate(
    product: Optional[Product], thresholds: dict[str, int], rules: Optional[RulesBySeverity]
) -> list[dict[str, Any]]:
    """
    Per severity: active observations, how many count under the rules, and whether the threshold holds.
    Without a product the instance-wide gate is previewed over the products that use it, and a severity
    passes when none of them exceeds its threshold.
    """
    scope = Q() if product else SETTINGS_GATE_OBSERVATIONS
    counted_filter = scope & get_security_gate_condition_filter(rules) if rules else scope
    active = count_active_observations_by_severity(product, None, scope)
    counted = count_active_observations_by_severity(product, None, counted_filter) if rules else active
    products_failed = None if product else _count_products_failing(thresholds, counted_filter)

    rows = []
    for severity, title in SEVERITY_TITLES.items():
        row: dict[str, Any] = {
            "severity": title,
            "threshold": thresholds[severity],
            "active": active[title],
            "counted": counted[title],
        }
        if products_failed is None:
            row["passed"] = counted[title] <= thresholds[severity]
        else:
            row["products_failed"] = products_failed[title]
            row["passed"] = products_failed[title] == 0
        rows.append(row)
    return rows


def _count_products_failing(thresholds: dict[str, int], counted_filter: Q) -> dict[str, int]:
    """Per title case severity, how many products have more counted observations than the threshold."""
    failing = {title: 0 for title in SEVERITY_TITLES.values()}
    for counts in count_active_observations_by_product_and_severity(counted_filter).values():
        for severity, title in SEVERITY_TITLES.items():
            if counts.get(title, 0) > thresholds[severity]:
                failing[title] += 1
    return failing
