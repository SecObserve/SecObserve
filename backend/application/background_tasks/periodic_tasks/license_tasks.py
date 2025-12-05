from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from application.background_tasks.services.task_base import so_periodic_task
from application.commons import settings_static
from application.commons.models import Settings
from application.licenses.services.license import import_licenses
from application.licenses.services.license_group import import_scancode_licensedb


@db_periodic_task(
    crontab(
        minute=settings_static.license_import_crontab_minute,
        hour=settings_static.license_import_crontab_hour,
    )
)
@so_periodic_task("Import SPDX licenses")
def task_spdx_license_import() -> str:
    settings = Settings.load()
    if not settings.feature_license_management:
        return "License management feature is disabled."

    message = import_licenses()

    import_scancode_licensedb()
    message += "\nLicense Groups from ScanCode LicenseDB imported"

    return message
