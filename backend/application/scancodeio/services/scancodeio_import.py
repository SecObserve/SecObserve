import logging
from datetime import timedelta
from typing import Any, Tuple

from django.db import transaction
from django.utils import timezone
from huey.contrib.djhuey import on_commit_task

from application.background_tasks.models import Periodic_Task
from application.background_tasks.services.task_base import delete_older_task_entries
from application.background_tasks.types import Status
from application.commons.models import Settings
from application.commons.services.log_message import format_log_message
from application.import_observations.models import Vulnerability_Check
from application.import_observations.services.import_observations import (
    process_license_components,
)
from application.notifications.services.tasks import handle_task_exception
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.queries.scancodeio_project import (
    get_scancodeio_project_by_id,
)
from application.scancodeio.services.results import (
    apply_osv_linux_distribution,
    get_license_components,
)
from application.scancodeio.services.scancodeio import get_scancodeio_results

logger = logging.getLogger("secobserve.scancodeio")

SCANCODEIO_RUN_STATUS_SUCCESS = "success"

TASK_NAME = "Import ScanCode.io results"

# A product has only one ScanCode.io project, so its components are identified by a fixed name
SCANCODEIO_FILENAME = "ScanCode.io"


def process_scancodeio_webhook(scancodeio_project: ScanCodeIO_Project, payload: dict[str, Any]) -> None:
    run = payload.get("run")
    if not isinstance(run, dict):
        run = {}
    logger.info(
        format_log_message(
            message=f"ScanCode.io webhook for project {scancodeio_project.project_name}: "
            + f"pipeline {run.get('pipeline_name')} finished with status {run.get('status')}"
        )
    )

    # The webhook only contains the project and the run, the results are read in the background
    if run.get("status") == SCANCODEIO_RUN_STATUS_SUCCESS:
        import_scancodeio_results_task(scancodeio_project.pk)


@on_commit_task()
def import_scancodeio_results_task(scancodeio_project_id: int) -> None:
    _process_scancodeio_import(scancodeio_project_id)


def _process_scancodeio_import(scancodeio_project_id: int) -> None:
    task_record = Periodic_Task(
        task=TASK_NAME,
        start_time=timezone.now(),
        status=Status.STATUS_RUNNING,
    )
    task_record.save()

    delete_older_task_entries(TASK_NAME)

    scancodeio_project = None
    try:
        scancodeio_project = get_scancodeio_project_by_id(scancodeio_project_id)
        if scancodeio_project:
            new, updated, deleted = import_scancodeio_results(scancodeio_project)
            message = (
                f"Product '{scancodeio_project.product.name}': {new} license components new, "
                f"{updated} updated, {deleted} deleted"
            )
        else:
            message = f"ScanCode.io project {scancodeio_project_id} not found, nothing to import"

        task_record.status = Status.STATUS_SUCCESS
        task_record.duration = (timezone.now() - task_record.start_time) / timedelta(milliseconds=1)
        task_record.message = message[:255]
        task_record.save()
    except Exception as e:
        task_record.status = Status.STATUS_FAILURE
        task_record.duration = (timezone.now() - task_record.start_time) / timedelta(milliseconds=1)
        task_record.message = str(e)[:255]
        task_record.save()

        handle_task_exception(e, product=scancodeio_project.product if scancodeio_project else None)
        raise


def import_scancodeio_results(scancodeio_project: ScanCodeIO_Project) -> Tuple[int, int, int]:
    # Only license components are imported, and the Linux distribution is only needed for their OSV scan
    if not Settings.load().feature_license_management:
        return 0, 0, 0

    # The request can take a while, so it is done before the transaction is started
    results = get_scancodeio_results(scancodeio_project)
    license_components, scanner = get_license_components(results)
    product = scancodeio_project.product

    with transaction.atomic():
        apply_osv_linux_distribution(product, results)

        vulnerability_check, _ = Vulnerability_Check.objects.update_or_create(
            product=product,
            branch=None,
            service=None,
            filename=SCANCODEIO_FILENAME,
            api_configuration_name="",
            defaults={
                "last_import_observations_new": None,
                "last_import_observations_updated": None,
                "last_import_observations_resolved": None,
                "last_import_licenses_new": None,
                "last_import_licenses_updated": None,
                "last_import_licenses_deleted": None,
                "scanner": scanner,
            },
        )

        return process_license_components(license_components, scanner, vulnerability_check)
