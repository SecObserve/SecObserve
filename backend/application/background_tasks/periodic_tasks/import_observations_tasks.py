import logging

from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from application.background_tasks.services.task_base import so_periodic_task
from application.commons import settings_static
from application.commons.models import Settings
from application.import_observations.models import Api_Configuration, Product
from application.import_observations.scanners.osv_scanner import scan_product
from application.import_observations.services.import_observations import (
    ApiImportParameters,
    api_import_observations,
)
from application.notifications.services.tasks import handle_task_exception

logger = logging.getLogger("secobserve.import_observations")


@db_periodic_task(
    crontab(
        minute=settings_static.api_import_crontab_minute,
        hour=settings_static.api_import_crontab_hour,
    )
)
@so_periodic_task("Import observations from API configurations and OSV")
def task_api_import() -> str:
    message = ""

    # 1. Import observations from API configurations
    settings = Settings.load()
    if not settings.feature_automatic_api_import:
        logger.info("API import is disabled in settings")
        message += "API import is disabled in settings."
    else:
        product_set = set()
        api_imports_failed = 0

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
                logger.warning("API import - %s: failed with exception", api_configuration)
                handle_task_exception(e, product=api_configuration.product)

        message += f" Imported observations for {len(product_set)} products from API configurations."
        if api_imports_failed > 0:
            message += f" API import failed for {api_imports_failed} configurations."

    # 2. Scan products for OSV vulnerabilities
    settings = Settings.load()
    if not settings.feature_automatic_osv_scanning:
        logger.info("OSV scanning is disabled in settings")
        return message + "\nOSV scanning is disabled in settings."

    osv_imports_failed = 0
    products = Product.objects.filter(osv_enabled=True, automatic_osv_scanning_enabled=True)
    for product in products:
        try:
            (
                observations_new,
                observations_updated,
                observations_resolved,
            ) = scan_product(product)
            logger.info(
                "OSV scanning - %s: %s new, %s updated, %s resolved",
                product,
                observations_new,
                observations_updated,
                observations_resolved,
            )
        except Exception as e:
            osv_imports_failed += 1
            logger.warning("OSV scanning - %s: failed with exception", product)
            handle_task_exception(e, product=product)

    message += f"\nImported observations for {len(products)} products from OSV scanning."
    if osv_imports_failed > 0:
        message += f" OSV scanning failed for {osv_imports_failed} products."

    return message
