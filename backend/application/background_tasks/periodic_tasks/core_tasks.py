from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from application.background_tasks.services.task_base import so_periodic_task
from application.commons import settings_static
from application.core.services.housekeeping import (
    housekeeping,
)
from application.core.services.risk_acceptance_expiry_task import (
    expire_risk_acceptances,
)


@db_periodic_task(
    crontab(
        minute=settings_static.branch_housekeeping_crontab_minute,
        hour=settings_static.branch_housekeeping_crontab_hour,
    )
)
@so_periodic_task("Housekeeping")
def task_housekeeping() -> str:
    message = housekeeping()
    return message


@db_periodic_task(
    crontab(
        minute=settings_static.risk_acceptance_expiry_crontab_minute,
        hour=settings_static.risk_acceptance_expiry_crontab_hour,
    )
)
@so_periodic_task("Expire risk acceptances")
def task_expire_risk_acceptances() -> str:
    message = expire_risk_acceptances()
    return message
