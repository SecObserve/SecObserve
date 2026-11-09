from itertools import batched
from typing import Optional, Union

from django.db.models import QuerySet

from application.commons.models import Settings
from application.core.models import Branch, Observation, Product
from application.core.queries.product import (
    get_product_by_id,
    populate_product_count_annotations,
)
from application.notifications.services.send_notifications_security_gate import (
    send_product_security_gate_notification,
)

SEVERITIES = ("critical", "high", "medium", "low", "none", "unknown")
SECURITY_GATES_BATCH_SIZE = 1000


def check_security_gate(product: Product) -> None:
    if product.is_product_group:
        raise ValueError(f"{product.name} is a product group")

    new_security_gate_passed = None

    thresholds = get_security_gate_thresholds(product)
    if thresholds is not None:
        annotated_product = get_product_by_id(
            product_id=product.pk, is_product_group=False, with_observation_annotations=True
        )
        if not annotated_product:
            raise ValueError(f"Product {product.pk} not found while calculating security gate.")

        new_security_gate_passed = evaluate_security_gate(annotated_product, thresholds)

    _update_security_gate(product, new_security_gate_passed)


def check_security_gates(products: QuerySet[Product]) -> None:
    # Many products at once, e.g. when the thresholds they inherit have changed: the observations are counted for a
    # batch of products in one query, without the license counts that check_security_gate() loads as well.
    settings = Settings.load()
    for batch in batched(products.select_related("product_group"), SECURITY_GATES_BATCH_SIZE):
        thresholds_of_products = [(product, get_security_gate_thresholds(product, settings)) for product in batch]
        populate_product_count_annotations(
            [product for product, thresholds in thresholds_of_products if thresholds is not None],
            is_product_group=False,
        )
        for product, thresholds in thresholds_of_products:
            security_gate_passed = evaluate_security_gate(product, thresholds) if thresholds is not None else None
            _update_security_gate(product, security_gate_passed)


def _update_security_gate(product: Product, new_security_gate_passed: Optional[bool]) -> None:
    if product.security_gate_passed != new_security_gate_passed:
        product.security_gate_passed = new_security_gate_passed
        product.save()
        send_product_security_gate_notification(product)


def check_security_gate_observation(observation: Observation) -> None:
    if observation.branch == observation.product.repository_default_branch:
        check_security_gate(observation.product)


def get_security_gate_thresholds(product: Product, settings: Optional[Settings] = None) -> Optional[dict[str, int]]:
    # Returns None if no security gate is to be applied for the product
    product_group = product.product_group

    security_gate_active: Optional[bool]
    if product_group and product_group.security_gate_active is not None:
        security_gate_active = product_group.security_gate_active
    else:
        security_gate_active = product.security_gate_active

    if security_gate_active is False:
        return None

    if security_gate_active is True:
        source = product_group if product_group and product_group.security_gate_active is True else product
        return {severity: getattr(source, f"security_gate_threshold_{severity}") or 0 for severity in SEVERITIES}

    settings = settings or Settings.load()
    if not settings.security_gate_active:
        return None

    return {severity: getattr(settings, f"security_gate_threshold_{severity}") for severity in SEVERITIES}


def evaluate_security_gate(counted: Union[Product, Branch], thresholds: dict[str, int]) -> bool:
    # counted needs to be annotated with the active observation counts per severity
    for severity, threshold in thresholds.items():
        count = getattr(counted, f"active_{severity}_observation_count", None)
        if count is None:
            raise ValueError("Observation counts are None.")
        if count > threshold:
            return False

    return True
