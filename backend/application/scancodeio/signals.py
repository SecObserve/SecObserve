from typing import Any

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.services.scancodeio import (
    delete_orphaned_scancodeio_project,
)


@receiver(pre_delete, sender=ScanCodeIO_Project)
def scancodeio_project_pre_delete(  # pylint: disable=unused-argument
    sender: Any, instance: ScanCodeIO_Project, **kwargs: Any
) -> None:
    # sender is needed according to Django documentation
    # The signal is also sent for the cascades from the product, branch and service, which would leave the
    # project in ScanCode.io behind. After delete_scancodeio_project(), the request only gets a harmless 404.
    delete_orphaned_scancodeio_project(str(instance.project_uuid))
