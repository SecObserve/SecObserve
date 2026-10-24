from datetime import date, timedelta
from typing import Optional

from application.commons.models import Settings
from application.core.models import Observation, Product
from application.core.types import Status

EXPIRY_STATUSES = (Status.STATUS_RISK_ACCEPTED, Status.STATUS_NOT_AFFECTED)


def calculate_expiry_date(product: Product, status: str) -> Optional[date]:
    if status == Status.STATUS_RISK_ACCEPTED:
        return calculate_risk_acceptance_expiry_date(product)
    if status == Status.STATUS_NOT_AFFECTED:
        return calculate_not_affected_expiry_date(product)
    return None


def update_expiry_date(observation: Observation, previous_status: str) -> None:
    # Spares the settings query of has_expiry() for every observation of an import
    if observation.current_status == previous_status and not observation.risk_acceptance_expiry_date:
        return
    if not has_expiry(observation):
        observation.risk_acceptance_expiry_date = None
    elif observation.current_status != previous_status:
        observation.risk_acceptance_expiry_date = calculate_expiry_date(observation.product, observation.current_status)


def has_expiry(observation: Observation) -> bool:
    if observation.current_status not in EXPIRY_STATUSES:
        return False
    if observation.current_status == Status.STATUS_NOT_AFFECTED and _status_is_imported(observation):
        return Settings.load().not_affected_expiry_imported
    return True


def _status_is_imported(observation: Observation) -> bool:
    # Neither assessment nor rule, so the status comes from a VEX statement or the scanner
    return not (observation.assessment_status or observation.rule_rego_status or observation.rule_status)


def calculate_risk_acceptance_expiry_date(product: Product) -> Optional[date]:
    return _expiry_date_from_settings(product, "risk_acceptance")


def calculate_not_affected_expiry_date(product: Product) -> Optional[date]:
    return _expiry_date_from_settings(product, "not_affected")


def _expiry_date_from_settings(product: Product, prefix: str) -> Optional[date]:
    for level in (product, product.product_group):
        if level is None:
            continue
        active = getattr(level, f"{prefix}_expiry_active")
        if active is False:
            return None
        days = getattr(level, f"{prefix}_expiry_days")
        if active and days and days > 0:
            return date.today() + timedelta(days=days)

    days = getattr(Settings.load(), f"{prefix}_expiry_days")
    return date.today() + timedelta(days=days) if days > 0 else None
