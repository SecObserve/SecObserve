from huey.contrib.djhuey import db_periodic_task

from application.background_tasks.services.crontab import crontab_in_time_zone
from application.background_tasks.services.task_base import so_periodic_task
from application.commons import settings_static
from application.epss.services.cvss_bt import import_cvss_bt
from application.epss.services.epss import epss_apply_observations, import_epss


@db_periodic_task(
    crontab_in_time_zone(
        minute=settings_static.background_epss_import_crontab_minute,
        hour=settings_static.background_epss_import_crontab_hour,
    )
)
@so_periodic_task("Import EPSS and cvss-bt")
def task_import_epss() -> str:
    message = import_epss() + "\n"
    message += epss_apply_observations() + "\n"
    message += import_cvss_bt()

    return message
