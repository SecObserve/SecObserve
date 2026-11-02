from datetime import date, timedelta
from typing import Optional

from application.commons.models import Settings
from application.core.models import Observation, Product
from application.core.types import Status

EXPIRY_STATUSES = (Status.STATUS_RISK_ACCEPTED,)


def calculate_expiry_date(product: Product, status: str) -> Optional[date]:
    if status == Status.STATUS_RISK_ACCEPTED:
        return calculate_risk_acceptance_expiry_date(product)
    return None


def update_expiry_date(observation: Observation, previous_status: str) -> None:
    if observation.current_status not in EXPIRY_STATUSES:
        observation.risk_acceptance_expiry_date = None
    elif observation.current_status != previous_status:
        observation.risk_acceptance_expiry_date = calculate_expiry_date(observation.product, observation.current_status)


def calculate_risk_acceptance_expiry_date(product: Product) -> Optional[date]:
    if product.risk_acceptance_expiry_active is False:
        return None
    if (
        product.risk_acceptance_expiry_active
        and product.risk_acceptance_expiry_days
        and product.risk_acceptance_expiry_days > 0
    ):
        return date.today() + timedelta(days=product.risk_acceptance_expiry_days)

    if product.product_group:
        if product.product_group.risk_acceptance_expiry_active is False:
            return None
        if (
            product.product_group.risk_acceptance_expiry_active
            and product.product_group.risk_acceptance_expiry_days
            and product.product_group.risk_acceptance_expiry_days > 0
        ):
            return date.today() + timedelta(days=product.product_group.risk_acceptance_expiry_days)

    settings = Settings.load()
    if settings.risk_acceptance_expiry_days > 0:
        return date.today() + timedelta(days=settings.risk_acceptance_expiry_days)

    return None
