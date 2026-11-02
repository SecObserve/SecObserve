import time
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings as django_settings
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from huey.contrib.djhuey import db_task

from application.notifications.models import Webhook, Webhook_Delivery
from application.notifications.services.send_notifications_exception import (
    send_task_exception_notification,
)
from application.notifications.services.tasks import handle_task_exception
from application.notifications.services.webhook_send import (
    Webhook_Send_Result,
    send_webhook_request,
)
from application.notifications.types import Webhook_Delivery_Status

KICK_DELAY = timedelta(seconds=2)
BATCH_SIZE = 100

_kicked_at: dict[int, float] = {}


class WebhookDeliveryError(Exception):
    """Reported once when a webhook has failed WEBHOOK_FAILURE_ALERT_THRESHOLD times in a row."""


def kick_webhooks(webhook_ids: Iterable[int]) -> None:
    """Claiming next_attempt_at first coalesces an import's events and never touches a lease or a backoff."""
    now = time.monotonic()
    for webhook_id in webhook_ids:
        # An import's events kick in a burst after commit; per process only, a race costs one extra kick
        if now - _kicked_at.get(webhook_id, float("-inf")) < KICK_DELAY.total_seconds():
            continue
        _kicked_at[webhook_id] = now
        if _claim(webhook_id, KICK_DELAY):
            deliver_webhook.schedule(args=(webhook_id,), delay=KICK_DELAY.seconds)


def dispatch_webhooks() -> None:
    """Safety net for lost kicks and expired leases and backoffs."""
    pending = Webhook_Delivery.objects.filter(webhook=OuterRef("pk"), status=Webhook_Delivery_Status.PENDING)
    webhook_ids = Webhook.objects.filter(_due(timezone.now()), Exists(pending), active=True).values_list(
        "pk", flat=True
    )
    for webhook_id in webhook_ids:
        deliver_webhook.schedule(args=(webhook_id,), delay=0)


@db_task()
def deliver_webhook(webhook_id: int) -> None:
    """No transaction spans a request; when the worker dies, its lease expires and the sweep resumes."""
    try:
        _drain(webhook_id)
    except Exception as e:
        handle_task_exception(e)
        raise


def _drain(webhook_id: int) -> None:
    lease_duration = _lease()
    lease = _claim(webhook_id, lease_duration)
    if not lease:
        return

    webhook = Webhook.objects.get(pk=webhook_id)
    pending = Webhook_Delivery.objects.filter(webhook_id=webhook_id, status=Webhook_Delivery_Status.PENDING)

    for delivery in pending.order_by("pk")[:BATCH_SIZE]:
        result = send_webhook_request(webhook.url, webhook.secret, str(delivery.event_id), delivery.payload)
        backoff = _save_result(webhook, delivery, result)
        next_attempt_at = timezone.now() + (backoff or lease_duration)
        if not _move_lease(webhook, lease, next_attempt_at):
            return
        if webhook.consecutive_failures == django_settings.WEBHOOK_FAILURE_ALERT_THRESHOLD:
            _send_alert(webhook, result)
        if backoff:
            return
        lease = next_attempt_at

    # Events emitted during the drain found the lease taken, so their kick did not schedule anything
    if _move_lease(webhook, lease, None) and pending.exists():
        deliver_webhook.schedule(args=(webhook_id,), delay=0)


def _lease() -> timedelta:
    # Covers connect, headers and the bounded error read; a receiver dripping bytes can still outlast it
    return timedelta(seconds=max(60, 3 * django_settings.WEBHOOK_TIMEOUT))


def _due(now: datetime) -> Q:
    return Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now)


def _claim(webhook_id: int, duration: timedelta) -> Optional[datetime]:
    now = timezone.now()
    until = now + duration
    claimed = Webhook.objects.filter(_due(now), pk=webhook_id, active=True).update(next_attempt_at=until)
    return until if claimed else None


def _move_lease(webhook: Webhook, lease: datetime, next_attempt_at: Optional[datetime]) -> bool:
    """False when the lease has been lost: webhook deleted, deactivated, reset or claimed by another drain."""
    updated = Webhook.objects.filter(pk=webhook.pk, next_attempt_at=lease, active=True).update(
        next_attempt_at=next_attempt_at, consecutive_failures=webhook.consecutive_failures
    )
    return updated == 1


def _save_result(webhook: Webhook, delivery: Webhook_Delivery, result: Webhook_Send_Result) -> Optional[timedelta]:
    """Updates the delivery and webhook.consecutive_failures, returns the endpoint backoff when the drain stops."""
    retry_delays = django_settings.WEBHOOK_RETRY_DELAYS
    attempts = delivery.attempts + 1

    if result.succeeded:
        webhook.consecutive_failures = 0
        status = Webhook_Delivery_Status.SUCCEEDED
    else:
        webhook.consecutive_failures += 1
        if result.retryable and attempts <= len(retry_delays):
            status = Webhook_Delivery_Status.PENDING
        else:
            status = Webhook_Delivery_Status.FAILED

    Webhook_Delivery.objects.filter(pk=delivery.pk).update(
        status=status,
        attempts=attempts,
        last_attempt_at=timezone.now(),
        response_status_code=result.status_code,
        error=result.error,
    )

    if result.succeeded:
        return None
    if not result.retryable and webhook.consecutive_failures < django_settings.WEBHOOK_FAILURE_ALERT_THRESHOLD:
        return None
    return timedelta(seconds=retry_delays[min(webhook.consecutive_failures, len(retry_delays)) - 1])


def _send_alert(webhook: Webhook, result: Webhook_Send_Result) -> None:
    send_task_exception_notification(
        function="deliver_webhook",
        arguments={"webhook_id": webhook.pk},
        user=None,
        exception=WebhookDeliveryError(
            f'Webhook "{webhook.name}" has failed {webhook.consecutive_failures} times in a row, '
            f"last error: {result.error}"
        ),
        product=webhook.product,
    )
