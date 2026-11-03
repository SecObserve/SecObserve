from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from application.core.types import Security_Gate_Operator, Severity

CONDITION_KEYS = (
    "known_exploited",
    "exploit_tooling",
    "proof_of_concept",
    "epss_min",
    "network_vector",
    "fix_available",
)
RULE_KEYS = ("operator",) + CONDITION_KEYS
SECURITY_GATE_ADVANCED_FIELDS = ("security_gate_advanced", "security_gate_conditions")

_BOOLEAN_CONDITION_KEYS = tuple(key for key in CONDITION_KEYS if key != "epss_min")
_SEVERITIES = {choice[0] for choice in Severity.SEVERITY_CHOICES}
_OPERATORS = {Security_Gate_Operator.OPERATOR_ANY, Security_Gate_Operator.OPERATOR_ALL}


def rule_has_condition(rule: Mapping[str, Any]) -> bool:
    """True when a boolean condition is true or epss_min is not None."""
    if any(rule.get(key) is True for key in _BOOLEAN_CONDITION_KEYS):
        return True
    return rule.get("epss_min") is not None


def normalize_security_gate_conditions(conditions: Any) -> dict[str, Any]:
    """
    Validates the JSON of the advanced security gate and returns it with every rule key present:
    booleans False, epss_min None and operator "any" unless given. Raises ValueError with a message
    that names the first problem.
    """
    if conditions is None:
        conditions = {}
    if not isinstance(conditions, Mapping):
        raise ValueError("Conditions must be an object with 'default' and 'severities'")
    for key in conditions:
        if key not in ("default", "severities"):
            raise ValueError(f"Unknown key '{key}'")

    severities_in = conditions.get("severities") or {}
    if not isinstance(severities_in, Mapping):
        raise ValueError("Severities must be an object keyed by severity")
    severities = {}
    for severity, rules in severities_in.items():
        if severity not in _SEVERITIES:
            raise ValueError(f"Unknown severity '{severity}'")
        severities[severity] = _normalize_rules(rules)

    return {"default": _normalize_rules(conditions.get("default")), "severities": severities}


def conditions_have_a_rule(conditions: Mapping[str, Any]) -> bool:
    """True when the default set or any severity holds at least one rule (after normalisation)."""
    if conditions.get("default"):
        return True
    return any(conditions.get("severities", {}).values())


def _normalize_rules(rules: Any) -> list[dict[str, Any]]:
    if rules is None:
        return []
    if not isinstance(rules, list):
        raise ValueError("Rules must be a list")
    return [_normalize_rule(rule) for rule in rules]


def _normalize_rule(rule: Any) -> dict[str, Any]:
    if not isinstance(rule, Mapping):
        raise ValueError("A rule must be an object")
    for key in rule:
        if key not in RULE_KEYS:
            raise ValueError(f"Unknown condition '{key}'")

    operator = rule.get("operator") or Security_Gate_Operator.OPERATOR_ANY
    if operator not in _OPERATORS:
        raise ValueError("Operator must be 'any' or 'all'")
    normalized: dict[str, Any] = {"operator": operator}

    for key in _BOOLEAN_CONDITION_KEYS:
        value = rule.get(key)
        if value is None:
            value = False
        if not isinstance(value, bool):
            raise ValueError(f"'{key}' must be true or false")
        normalized[key] = value

    epss_min = rule.get("epss_min")
    if epss_min is not None:
        if isinstance(epss_min, bool) or not isinstance(epss_min, (int, float, Decimal)) or not 0 <= epss_min <= 100:
            raise ValueError("EPSS must be a number between 0 and 100")
    normalized["epss_min"] = epss_min

    if not rule_has_condition(normalized):
        raise ValueError("A rule needs at least one enabled condition")

    return normalized
