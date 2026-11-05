from itertools import batched
from typing import Optional, Union

from django.db.models import QuerySet

from application.commons.models import Settings
from application.core.models import Branch, Observation, Product
from application.core.queries.observation import (
    count_active_observations_by_priority,
    count_active_observations_by_product_and_priority,
)
from application.core.queries.product import (
    get_product_by_id,
    populate_product_count_annotations,
)
from application.notifications.services.send_notifications_security_gate import (
    send_product_security_gate_notification,
)

SEVERITIES = ("critical", "high", "medium", "low", "none", "unknown")
SECURITY_GATE_FIELDS: tuple[str, ...] = (
    "security_gate_active",
    *[f"security_gate_threshold_{severity}" for severity in SEVERITIES],
    "security_gate_priority_thresholds",
)
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

        new_security_gate_passed = evaluate_security_gate(
            annotated_product, thresholds, get_security_gate_priority_thresholds(product)
        )

    _update_security_gate(product, new_security_gate_passed)


def check_security_gates(products: QuerySet[Product]) -> None:
    # Many products at once, e.g. when the thresholds they inherit have changed: the observations are counted for a
    # batch of products in one query, without the license counts that check_security_gate() loads as well.
    settings = Settings.load()
    for batch in batched(products.select_related("product_group"), SECURITY_GATES_BATCH_SIZE):
        thresholds_of_products = [
            (
                product,
                get_security_gate_thresholds(product, settings),
                get_security_gate_priority_thresholds(product, settings),
            )
            for product in batch
        ]
        populate_product_count_annotations(
            [product for product, thresholds, _ in thresholds_of_products if thresholds is not None],
            is_product_group=False,
        )
        products_with_priorities = [product for product, _, priorities in thresholds_of_products if priorities]
        if products_with_priorities:
            priority_counts = count_active_observations_by_product_and_priority(products_with_priorities)
            for product in products_with_priorities:
                product.active_observation_counts_by_priority = priority_counts.get(product.pk, {})
        for product, thresholds, priority_thresholds in thresholds_of_products:
            security_gate_passed = (
                evaluate_security_gate(product, thresholds, priority_thresholds) if thresholds is not None else None
            )
            _update_security_gate(product, security_gate_passed)


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
    # Returns None if no security gate is to be applied for the product
    product_group = product.product_group
    if product_group and product_group.security_gate_active is not None:
        return product_group if product_group.security_gate_active else None

    if product.security_gate_active is not None:
        return product if product.security_gate_active else None

    settings = settings or Settings.load()
    return settings if settings.security_gate_active else None


def get_security_gate_thresholds(product: Product, settings: Optional[Settings] = None) -> Optional[dict[str, int]]:
    source = _get_security_gate_source(product, settings)
    if source is None:
        return None

    return {severity: getattr(source, f"security_gate_threshold_{severity}") or 0 for severity in SEVERITIES}


def get_security_gate_priority_thresholds(
    product: Product, settings: Optional[Settings] = None
) -> Optional[dict[int, int]]:
    source = _get_security_gate_source(product, settings)
    if source is None:
        return None

    return {pair["priority"]: pair["threshold"] for pair in source.security_gate_priority_thresholds or []}


def get_priority_counts(counted: Union[Product, Branch]) -> dict[int, int]:
    if isinstance(counted, Branch):
        return count_active_observations_by_priority(counted.product, counted)
    return count_active_observations_by_priority(counted)


def evaluate_security_gate(
    counted: Union[Product, Branch], thresholds: dict[str, int], priority_thresholds: Optional[dict[int, int]] = None
) -> bool:
    # counted needs to be annotated with the active observation counts per severity
    for severity, threshold in thresholds.items():
        count = getattr(counted, f"active_{severity}_observation_count", None)
        if count is None:
            raise ValueError("Observation counts are None.")
        if count > threshold:
            return False

    if not priority_thresholds:
        return True

    # check_security_gates() counts the priorities of a whole batch in one query
    priority_counts = getattr(counted, "active_observation_counts_by_priority", None)
    if priority_counts is None:
        priority_counts = get_priority_counts(counted)
    return all(priority_counts.get(priority, 0) <= threshold for priority, threshold in priority_thresholds.items())
