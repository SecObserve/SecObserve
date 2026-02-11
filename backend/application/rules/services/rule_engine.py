import json
import re
from copy import copy
from datetime import date
from typing import Any, Optional

import jsonpickle

from application.access_control.services.current_user import get_current_user
from application.core.models import Observation, Product
from application.core.services.observation import (
    get_current_priority,
    get_current_severity,
    get_current_status,
    get_current_vex_justification,
)
from application.core.services.observation_log import create_observation_log
from application.core.services.risk_acceptance_expiry import (
    calculate_risk_acceptance_expiry_date,
)
from application.core.services.security_gate import check_security_gate
from application.core.types import Assessment_Status, Status
from application.issue_tracker.services.issue_tracker import (
    push_observation_to_issue_tracker,
)
from application.rules.models import Rule
from application.rules.services.rego_interpreter import RegoInterpreter
from application.rules.types import Rule_Status, Rule_Type


class Rule_Engine:
    def __init__(self, product: Product) -> None:
        self.product = product

        product_parser_rules = Rule.objects.filter(
            product=product,
            enabled=True,
            approval_status__in=[
                Rule_Status.RULE_STATUS_APPROVED,
                Rule_Status.RULE_STATUS_AUTO_APPROVED,
            ],
        )
        self.rules: list[Rule] = list(product_parser_rules)

        if product.product_group:
            product_group_parser_rules = Rule.objects.filter(
                product=product.product_group,
                enabled=True,
            )
            self.rules += list(product_group_parser_rules)

        if product.apply_general_rules:
            general_rules = Rule.objects.filter(
                product__isnull=True,
                enabled=True,
                approval_status__in=[
                    Rule_Status.RULE_STATUS_APPROVED,
                    Rule_Status.RULE_STATUS_AUTO_APPROVED,
                ],
            )
            self.rules += list(general_rules)

        self.rego_interpreters: dict[Any, RegoInterpreter] = {}
        for rule in self.rules:
            if rule.type == Rule_Type.RULE_TYPE_REGO:
                self.rego_interpreters[rule.pk] = RegoInterpreter(rule.rego_module)

    def apply_rules_for_observation(self, observation: Observation) -> None:
        observation_before = copy(observation)

        rule_fields_found = False
        for rule in self.rules:
            if rule.type == Rule_Type.RULE_TYPE_FIELDS:
                rule_fields_found = self.check_rule_for_observation(rule, observation, observation_before)
                if rule_fields_found:
                    break

        rule_rego_found = False
        for rule in self.rules:
            if rule.type == Rule_Type.RULE_TYPE_REGO:
                rule_rego_found = self.check_rule_for_observation(rule, observation, observation_before)
                if rule_rego_found:
                    break

        # Write observation and observation log if no rule was found but there was one before
        # if not rule_fields_found and (
        #     observation_before.general_rule != observation.general_rule
        #     or observation_before.product_rule != observation.product_rule
        # ):
        #     _write_observation_log_no_rule(
        #         observation, observation_before.product_rule, observation_before.general_rule
        #     )

    def apply_all_rules_for_product(self) -> None:
        if self.product.is_product_group:
            products = Product.objects.filter(product_group=self.product)
            observations = Observation.objects.filter(product__in=products)
        else:
            observations = Observation.objects.filter(product=self.product)

        observations = (
            observations.select_related("parser").select_related("general_rule").select_related("product_rule")
        )

        for observation in observations:
            self.apply_rules_for_observation(observation)

        if self.product.is_product_group:
            for product in self.product.products.all():
                check_security_gate(product)
        else:
            check_security_gate(self.product)

    def check_rule_for_observation(
        self,
        rule: Rule,
        observation: Observation,
        observation_before: Observation,
        simulation: Optional[bool] = False,
    ) -> bool:
        found = False
        if rule.type == Rule_Type.RULE_TYPE_FIELDS:
            found = self._check_rule_fields(rule, observation, observation_before, simulation)
            if simulation:
                return found

        if rule.type == Rule_Type.RULE_TYPE_REGO:
            found = self._check_rule_rego(rule, observation, observation_before, simulation)
            if simulation:
                return found

        # Write observation and observation and push to issue tracker log if status or severity has been changed
        if found and (  # pylint: disable=too-many-boolean-expressions
            observation_before.rule_priority != observation.rule_priority
            or observation_before.rule_rego_priority != observation.rule_rego_priority
            or observation_before.current_priority != observation.current_priority
            or observation_before.rule_status != observation.rule_status
            or observation_before.rule_rego_status != observation.rule_rego_status
            or observation_before.current_status != observation.current_status
            or observation_before.rule_severity != observation.rule_severity
            or observation_before.rule_rego_severity != observation.rule_rego_severity
            or observation_before.current_severity != observation.current_severity
            or observation_before.rule_vex_justification != observation.rule_vex_justification
            or observation_before.rule_rego_vex_justification != observation.rule_rego_vex_justification
            or observation_before.current_vex_justification != observation.current_vex_justification
            or observation_before.general_rule != observation.general_rule
            or observation_before.product_rule != observation.product_rule
            or observation_before.general_rule_rego != observation.general_rule_rego
            or observation_before.product_rule_rego != observation.product_rule_rego
        ):
            _write_observation_log(
                observation=observation,
                rule=rule,
                previous_severity=observation_before.current_severity,
                previous_status=observation_before.current_status,
                previous_vex_justification=observation_before.current_vex_justification,
                previous_risk_acceptance_expiry_date=observation_before.risk_acceptance_expiry_date,
            )
            push_observation_to_issue_tracker(observation, get_current_user())

            return True

        return False

    def _check_rule_fields(
        self, rule: Rule, observation: Observation, observation_before: Observation, simulation: Optional[bool] = False
    ) -> bool:
        if (  # pylint: disable=too-many-boolean-expressions
            (not rule.parser or observation.parser == rule.parser)
            and (not rule.scanner_prefix or observation.scanner.lower().startswith(rule.scanner_prefix.lower()))
            and _check_regex(rule.title, observation.title)
            and _check_regex(rule.description_observation, observation.description)
            and _check_regex(rule.origin_component_name_version, observation.origin_component_name_version)
            and _check_regex(rule.origin_component_purl, observation.origin_component_purl)
            and _check_regex(
                rule.origin_docker_image_name_tag,
                observation.origin_docker_image_name_tag,
            )
            and _check_regex(rule.origin_endpoint_url, observation.origin_endpoint_url)
            and _check_regex(rule.origin_service_name, observation.origin_service_name)
            and _check_regex(rule.origin_source_file, observation.origin_source_file)
            and _check_regex(
                rule.origin_cloud_qualified_resource,
                observation.origin_cloud_qualified_resource,
            )
            and _check_regex(
                rule.origin_kubernetes_qualified_resource,
                observation.origin_kubernetes_qualified_resource,
            )
        ):
            if simulation:
                return True

            if rule.new_severity:
                observation.rule_severity = rule.new_severity
                observation.current_severity = get_current_severity(observation)

            if rule.new_status:
                observation.rule_status = rule.new_status
                observation.current_status = get_current_status(observation)

            if rule.new_vex_justification:
                observation.rule_vex_justification = rule.new_vex_justification
                observation.current_vex_justification = get_current_vex_justification(observation)

            if observation.current_status == Status.STATUS_RISK_ACCEPTED:
                if observation_before.current_status != Status.STATUS_RISK_ACCEPTED:
                    observation.risk_acceptance_expiry_date = calculate_risk_acceptance_expiry_date(observation.product)
            else:
                observation.risk_acceptance_expiry_date = None

            if rule.product:
                observation.product_rule = rule
            else:
                observation.general_rule = rule

            return True

        return False

    def _check_rule_rego(
        self, rule: Rule, observation: Observation, observation_before: Observation, simulation: Optional[bool] = False
    ) -> bool:
        jsonpickle.set_encoder_options("simplejson", use_decimal=True, sort_keys=True)
        jsonpickle.set_preferred_backend("simplejson")

        observation_dict = json.loads(jsonpickle.dumps(observation, unpicklable=False, use_decimal=True))
        observation_dict = {k: v for k, v in observation_dict.items() if v is not None and v != ""}

        rego_interpreter = self.rego_interpreters[rule.pk]
        result = rego_interpreter.query(observation_dict)

        new_priority = result.get("priority")
        new_status = result.get("status")
        new_severity = result.get("severity")
        new_vex_justification = result.get("vex_justification")

        if new_priority or new_severity or new_status or new_vex_justification:
            if simulation:
                return True

            if new_priority:
                observation.rule_rego_priority = new_priority
                observation.current_priority = get_current_priority(observation)
            if new_severity:
                observation.rule_rego_severity = new_severity
                observation.current_severity = get_current_severity(observation)
            if new_status:
                observation.rule_rego_status = new_status
                observation.current_status = get_current_status(observation)

                if observation.current_status == Status.STATUS_RISK_ACCEPTED:
                    if observation_before.current_status != Status.STATUS_RISK_ACCEPTED:
                        observation.risk_acceptance_expiry_date = calculate_risk_acceptance_expiry_date(
                            observation.product
                        )
                else:
                    observation.risk_acceptance_expiry_date = None

            if new_vex_justification:
                observation.rule_rego_vex_justification = new_vex_justification
                observation.current_vex_justification = get_current_vex_justification(observation)

            if rule.product:
                observation.product_rule_rego = rule
            else:
                observation.general_rule_rego = rule

            return True

        return False


def _check_regex(pattern: str, value: str) -> bool:
    if not pattern:
        return True

    if not value:
        return False

    compiled_pattern = re.compile(pattern, re.IGNORECASE)
    return compiled_pattern.match(value) is not None


def _write_observation_log(
    *,
    observation: Observation,
    rule: Rule,
    previous_severity: str,
    previous_status: str,
    previous_vex_justification: str,
    previous_risk_acceptance_expiry_date: Optional[date],
) -> None:
    if previous_status != observation.current_status:
        status = observation.current_status
    else:
        status = ""
    if previous_severity != observation.current_severity:
        severity = observation.current_severity
    else:
        severity = ""
    if previous_vex_justification != observation.current_vex_justification:
        vex_justification = observation.current_vex_justification
    else:
        vex_justification = ""
    if previous_risk_acceptance_expiry_date != observation.risk_acceptance_expiry_date:
        risk_acceptance_expiry_date = observation.risk_acceptance_expiry_date
    else:
        risk_acceptance_expiry_date = None

    if rule.description:
        comment = rule.description
    else:
        if rule.product:
            comment = f"Updated by product rule {rule.name}"
        else:
            comment = f"Updated by general rule {rule.name}"

    create_observation_log(
        observation=observation,
        severity=severity,
        status=status,
        comment=comment,
        vex_justification=vex_justification,
        assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        risk_acceptance_expiry_date=risk_acceptance_expiry_date,
    )


def _write_observation_log_no_rule(
    observation: Observation,
    previous_product_rule: Optional[Rule],
    previous_general_rule: Optional[Rule],
) -> None:
    observation.rule_severity = ""
    previous_severity = observation.current_severity
    observation.current_severity = get_current_severity(observation)

    observation.rule_status = ""
    previous_status = observation.current_status
    observation.current_status = get_current_status(observation)

    observation.rule_vex_justification = ""
    previous_vex_justification = observation.current_vex_justification
    observation.current_vex_justification = get_current_vex_justification(observation)

    previous_risk_acceptance_expiry_date = observation.risk_acceptance_expiry_date
    if observation.current_status == Status.STATUS_RISK_ACCEPTED:
        if previous_status != Status.STATUS_RISK_ACCEPTED:
            observation.risk_acceptance_expiry_date = calculate_risk_acceptance_expiry_date(observation.product)
    else:
        observation.risk_acceptance_expiry_date = None

    log_status = observation.current_status if previous_status != observation.current_status else ""

    log_severity = observation.current_severity if previous_severity != observation.current_severity else ""

    log_vex_justification = (
        observation.current_vex_justification
        if previous_vex_justification != observation.current_vex_justification
        else ""
    )

    log_risk_acceptance_expiry_date = (
        observation.risk_acceptance_expiry_date
        if previous_risk_acceptance_expiry_date != observation.risk_acceptance_expiry_date
        else None
    )

    if previous_product_rule:
        comment = f"Removed product rule {previous_product_rule.name}"
    elif previous_general_rule:
        comment = f"Removed general rule {previous_general_rule.name}"
    else:
        comment = "Removed unknown rule"

    create_observation_log(
        observation=observation,
        severity=log_severity,
        status=log_status,
        comment=comment,
        vex_justification=log_vex_justification,
        assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        risk_acceptance_expiry_date=log_risk_acceptance_expiry_date,
    )
