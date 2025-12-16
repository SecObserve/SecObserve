from application.core.models import Observation, Product
from application.core.types import Status
from application.licenses.models import License_Component


def get_product_group_observation_count(product_group: Product, severity: str) -> int:
    if not product_group.is_product_group:
        raise ValueError(f"{product_group.name} is not a product group")

    count = 0
    for product in Product.objects.filter(product_group=product_group):
        count += get_product_observation_count(product, severity)
    return count


def get_product_observation_count(product: Product, severity: str) -> int:
    return Observation.objects.filter(
        product=product,
        branch=product.repository_default_branch,
        current_status=Status.STATUS_OPEN,
        current_severity=severity,
    ).count()


def get_product_group_license_count(product_group: Product, evaluation_result: str) -> int:
    count = 0
    for product in Product.objects.filter(product_group=product_group):
        count += get_product_license_count(product, evaluation_result)
    return count


def get_product_license_count(product: Product, evaluation_result: str) -> int:
    return License_Component.objects.filter(
        product=product,
        branch=product.repository_default_branch,
        evaluation_result=evaluation_result,
    ).count()
