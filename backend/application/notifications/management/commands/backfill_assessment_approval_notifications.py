from typing import Any

from django.core.management.base import BaseCommand

from application.core.models import Observation_Log
from application.core.types import Assessment_Status
from application.notifications.models import Notification
from application.notifications.services.send_notifications_assessment import (
    send_assessment_approval_request_notification,
)


class Command(BaseCommand):
    help = "Create in-app notifications for existing designated assessment approval requests."

    def handle(self, *args: Any, **options: Any) -> None:
        created_count = 0
        pending_logs = Observation_Log.objects.filter(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        ).select_related("observation", "observation__product", "observation__product__product_group", "user")

        for observation_log in pending_logs.iterator():
            existed = Notification.objects.filter(
                type=Notification.TYPE_ASSESSMENT_REQUEST,
                observation_log=observation_log,
            ).exists()
            notification = send_assessment_approval_request_notification(observation_log, send_external=False)
            if notification and not existed:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} assessment approval notifications."))
