from huey.contrib.djhuey import db_periodic_task

from application.background_tasks.services.crontab import crontab_in_time_zone
from application.background_tasks.services.task_base import so_periodic_task
from application.commons import settings_static
from application.commons.models import Settings
from application.epss.services.cvss_bt import import_cvss_bt
from application.epss.services.epss import epss_apply_observations, import_epss
from application.rules.services.evaluator import apply_rules_to_enriched_observations


@db_periodic_task(
    crontab_in_time_zone(
        minute=settings_static.background_epss_import_crontab_minute,
        hour=settings_static.background_epss_import_crontab_hour,
    )
)
@so_periodic_task("Import EPSS and cvss-bt")
def task_import_epss() -> str:
    settings = Settings.load()
    lines = [import_epss()]
    num_changed, crossed = epss_apply_observations(settings.apply_rules_epss_step)
    lines.append(f"Applied EPSS scores to {num_changed} observations.")
    changed_exploit: list[int] = []
    try:
        cvss_bt_message, changed_exploit = import_cvss_bt()
        lines.append(cvss_bt_message)
    finally:
        if settings.feature_apply_rules_after_epss_import:
            result = apply_rules_to_enriched_observations(set(crossed) | set(changed_exploit))
            lines.append(
                f"Rules applied to {result.observations_processed} observations, {result.observations_changed} changed."
            )
    return "\n".join(lines)
