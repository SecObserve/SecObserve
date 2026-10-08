from datetime import UTC, datetime
from typing import Callable
from zoneinfo import ZoneInfo

from django.conf import settings
from huey import crontab


def crontab_in_time_zone(minute: int, hour: int) -> Callable[[datetime], bool]:
    """Like huey's crontab, but with the hour and minute in BACKGROUND_TASKS_TIME_ZONE."""

    validate = crontab(minute=minute, hour=hour)
    time_zone = ZoneInfo(settings.BACKGROUND_TASKS_TIME_ZONE)

    def validate_datetime(timestamp: datetime) -> bool:
        # Huey runs with utc=True and passes the current time as naive UTC
        return validate(timestamp.replace(tzinfo=UTC).astimezone(time_zone))

    return validate_datetime
