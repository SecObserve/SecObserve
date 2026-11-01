from typing import Any

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from application.core.models import Product
from application.scancodeio.queries.scancodeio_project import (
    get_scancodeio_project_by_product,
)
from application.scancodeio.services.scancodeio import (
    delete_orphaned_scancodeio_project,
)


@receiver(pre_delete, sender=Product)
def product_pre_delete(sender: Any, instance: Product, **kwargs: Any) -> None:  # pylint: disable=unused-argument
    # sender is needed according to Django documentation
    # The ScanCodeIO_Project is deleted by the cascade, but the project in ScanCode.io would be left behind
    scancodeio_project = get_scancodeio_project_by_product(instance)
    if scancodeio_project:
        delete_orphaned_scancodeio_project(str(scancodeio_project.project_uuid))
