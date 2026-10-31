import logging
from datetime import timedelta
from typing import Optional
from uuid import uuid4

import requests
from django.conf import settings as django_settings
from django.db import InterfaceError, OperationalError
from huey.api import Task
from huey.contrib.djhuey import db_periodic_task, db_task

from application.background_tasks.services.crontab import crontab_in_time_zone
from application.background_tasks.services.task_base import (
    PeriodicTaskError,
    so_periodic_task,
)
from application.commons import settings_static
from application.commons.models import Settings
from application.import_observations.models import Api_Configuration, Product
from application.import_observations.scanners.osv_scanner import OSVScanner
from application.import_observations.scanners.vulnerablecode_scanner import (
    VulnerableCodeScanner,
)
from application.import_observations.services.import_observations import (
    ApiImportParameters,
    api_import_observations,
)
from application.notifications.services.send_notifications_exception import (
    send_task_exception_notification,
)
from application.notifications.services.tasks import handle_task_exception

logger = logging.getLogger("secobserve.import_observations")

# Below the default priority 0 of all other tasks, so that they are not queued behind the scans of all products
OSV_SCAN_PRIORITY = -1
# Scans still queued by then are dropped, so that the scans of two nightly runs don't pile up
OSV_SCAN_EXPIRES = timedelta(hours=20)


@db_periodic_task(
    crontab_in_time_zone(
        minute=settings_static.api_import_crontab_minute,
        hour=settings_static.api_import_crontab_hour,
    )
)
@so_periodic_task("Import observations from API configurations, OSV and VulnerableCode")
def task_api_import() -> str:
    message, api_imports_failed = _import_api()
    # Before the OSV scans are enqueued, so that both scanners don't import into the same product at the same time
    message, vulnerablecode_imports_failed = _import_vulnerablecode(message)
    message = _enqueue_osv_scans(message)

    if api_imports_failed + vulnerablecode_imports_failed > 0:
        # The imports of the other products have been executed, but the task has to be
        # marked as failed, so that the failures are not overlooked.
        raise PeriodicTaskError(message)

    return message


def _import_api() -> tuple[str, int]:
    message = ""
    api_imports_failed = 0

    settings = Settings.load()
    if not settings.feature_automatic_api_import:
        logger.info("API import is disabled in settings")
        message += "API import is disabled in settings."
    else:
        product_set = set()

        api_configurations = Api_Configuration.objects.filter(automatic_import_enabled=True)
        for api_configuration in api_configurations:
            product_set.add(api_configuration.product)
            try:
                service_name = (
                    api_configuration.automatic_import_service.name
                    if api_configuration.automatic_import_service
                    else ""
                )
                api_import_parameters = ApiImportParameters(
                    api_configuration=api_configuration,
                    branch=api_configuration.automatic_import_branch,
                    service_name=service_name,
                    docker_image_name_tag=api_configuration.automatic_import_docker_image_name_tag,
                    endpoint_url=api_configuration.automatic_import_endpoint_url,
                    kubernetes_cluster=api_configuration.automatic_import_kubernetes_cluster,
                    kubernetes_namespace="",
                    kubernetes_resource_type="",
                    kubernetes_resource_name="",
                )
                (
                    observations_new,
                    observations_updated,
                    observations_resolved,
                ) = api_import_observations(api_import_parameters)
                logger.info(
                    "API import - %s: %s new, %s updated, %s resolved",
                    api_configuration,
                    observations_new,
                    observations_updated,
                    observations_resolved,
                )
            except Exception as e:
                api_imports_failed += 1
                logger.exception("API import - %s: failed with exception", api_configuration)
                handle_task_exception(e, product=api_configuration.product)

        message += f"Imported observations for {len(product_set)} products from API configurations."
        if api_imports_failed > 0:
            message += f"\nAPI import failed for {api_imports_failed} configurations."

    return message, api_imports_failed


def _enqueue_osv_scans(message: str) -> str:
    settings = Settings.load()
    if not settings.feature_automatic_osv_scanning:
        logger.info("OSV scanning is disabled in settings")
        return message + "\nOSV scanning is disabled in settings."

    product_ids = list(
        Product.objects.filter(osv_enabled=True, automatic_osv_scanning_enabled=True).values_list("pk", flat=True)
    )
    run_id = uuid4().hex
    for product_id in product_ids:
        task_osv_scan_product(product_id, run_id)

    return message + f"\nEnqueued OSV scanning for {len(product_ids)} products."


@db_task(
    priority=OSV_SCAN_PRIORITY,
    retries=django_settings.OSV_SCAN_RETRIES,
    retry_delay=django_settings.OSV_SCAN_RETRY_DELAY,
    retry_backoff=2,
    expires=OSV_SCAN_EXPIRES,
    context=True,
)
def task_osv_scan_product(product_id: int, run_id: str, task: Optional[Task] = None) -> None:
    product = None
    try:
        # The product may have been deleted or its scanning disabled since the task has been enqueued
        product = Product.objects.filter(pk=product_id, osv_enabled=True, automatic_osv_scanning_enabled=True).first()
        if not product or not Settings.load().feature_automatic_osv_scanning:
            logger.info("OSV scanning - product %s: not found or not enabled anymore", product_id)
            return

        observations_new, observations_updated, observations_resolved = OSVScanner(run_id).scan_product(product)
        logger.info(
            "OSV scanning - %s: %s new, %s updated, %s resolved",
            product,
            observations_new,
            observations_updated,
            observations_resolved,
        )
    except Exception as e:
        if task and task.retries:
            if _is_transient(e):
                raise
            # Another attempt would fail the same way
            task.retries = 0
        # Without the arguments the rate limit is the same for all products, so that an outage of OSV
        # doesn't send a notification per product
        send_task_exception_notification(
            function="task_osv_scan_product", arguments=None, user=None, exception=e, product=product
        )
        raise


def _is_transient(e: Exception) -> bool:
    if isinstance(e, requests.HTTPError):
        return e.response is not None and (e.response.status_code == 429 or e.response.status_code >= 500)
    return isinstance(e, (requests.RequestException, OperationalError, InterfaceError))


def _import_vulnerablecode(message: str) -> tuple[str, int]:
    settings = Settings.load()
    if not settings.feature_automatic_vulnerablecode_scanning:
        logger.info("VulnerableCode scanning is disabled in settings")
        return message + "\nVulnerableCode scanning is disabled in settings.", 0

    if not settings.vulnerablecode_base_url:
        logger.info("VulnerableCode base URL is not set")
        return message + "\nVulnerableCode bade URL is not set.", 0

    vulnerablecode_imports_failed = 0
    vulnerablecode_scanner = VulnerableCodeScanner()
    products = Product.objects.filter(vulnerablecode_enabled=True, automatic_vulnerablecode_scanning_enabled=True)
    for product in products:
        try:
            (
                observations_new,
                observations_updated,
                observations_resolved,
            ) = vulnerablecode_scanner.scan_product(product)
            logger.info(
                "VulnerableCode scanning - %s: %s new, %s updated, %s resolved",
                product,
                observations_new,
                observations_updated,
                observations_resolved,
            )
        except Exception as e:
            vulnerablecode_imports_failed += 1
            logger.exception("VulnerableCode scanning - %s: failed with exception", product)
            handle_task_exception(e, product=product)

    message += f"\nImported observations for {len(products)} products from VulnerableCode scanning."
    if vulnerablecode_imports_failed > 0:
        message += f"\nVulnerableCode scanning failed for {vulnerablecode_imports_failed} products."

    return message, vulnerablecode_imports_failed
