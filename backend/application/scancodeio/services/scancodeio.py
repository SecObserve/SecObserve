import logging

from application.commons.services.log_message import format_log_message
from application.core.models import Product

logger = logging.getLogger("secobserve.scancodeio")


def create_scancodeio_project(product: Product) -> None:
    # Dummy implementation, the project will be created in ScanCode.io later
    logger.info(format_log_message(message=f"ScanCode.io project for product {product.name} requested"))
