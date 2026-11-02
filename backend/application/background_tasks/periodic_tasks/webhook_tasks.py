from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from application.notifications.services.webhook_delivery import dispatch_webhooks


# Not a so_periodic_task, that would write a Periodic_Task entry every minute
@db_periodic_task(crontab(minute="*"))
def task_dispatch_webhooks() -> None:
    dispatch_webhooks()
