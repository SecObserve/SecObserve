import uuid
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import call, patch

from django.test import override_settings

from application.notifications.models import Webhook, Webhook_Delivery
from application.notifications.services.webhook_delivery import (
    WebhookDeliveryError,
    deliver_webhook,
    dispatch_webhooks,
    kick_webhooks,
)
from application.notifications.services.webhook_send import Webhook_Send_Result
from application.notifications.types import Webhook_Delivery_Status
from unittests.base_test_case import BaseTestCase

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=dt_timezone.utc)


def _result(status_code: int) -> Webhook_Send_Result:
    return Webhook_Send_Result(status_code, "" if 200 <= status_code < 300 else f"HTTP {status_code}")


@override_settings(
    WEBHOOK_RETRY_DELAYS=[60, 300, 1800, 7200, 21600], WEBHOOK_FAILURE_ALERT_THRESHOLD=5, WEBHOOK_TIMEOUT=10
)
class TestWebhookDelivery(BaseTestCase):
    def setUp(self):
        super().setUp()
        self._patch("timezone.now", NOW)
        self.mock_send = self._patch("send_webhook_request", _result(200))
        self.mock_schedule = self._patch("deliver_webhook.schedule")
        self.mock_alert = self._patch("send_task_exception_notification")
        self.webhook = self._webhook()

    def _patch(self, name, return_value=None):
        patcher = patch(f"application.notifications.services.webhook_delivery.{name}", return_value=return_value)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _webhook(self, **kwargs) -> Webhook:
        return Webhook.objects.create(
            name="webhook",
            url="https://example.com/hook",
            secret="whsec_c2VjcmV0",
            event_types="observation.created",
            **kwargs,
        )

    def _delivery(self, webhook=None, **kwargs) -> Webhook_Delivery:
        return Webhook_Delivery.objects.create(
            webhook=webhook or self.webhook,
            event_id=uuid.uuid4(),
            event_type="observation.created",
            payload='{"type": "observation.created"}',
            **kwargs,
        )

    def _set_webhook(self, **fields):
        Webhook.objects.filter(pk=self.webhook.pk).update(**fields)

    def _deliver(self):
        deliver_webhook.call_local(self.webhook.pk)
        self.webhook.refresh_from_db()

    def test_success_marks_succeeded_and_releases_lease(self):
        self._set_webhook(consecutive_failures=2)
        delivery = self._delivery()

        self._deliver()

        delivery.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.SUCCEEDED, delivery.status)
        self.assertEqual(1, delivery.attempts)
        self.assertEqual(200, delivery.response_status_code)
        self.assertEqual(NOW, delivery.last_attempt_at)
        self.assertEqual(0, self.webhook.consecutive_failures)
        self.assertIsNone(self.webhook.next_attempt_at)
        self.mock_schedule.assert_not_called()

    def test_signature_covers_stored_payload(self):
        delivery = self._delivery()

        self._deliver()

        self.mock_send.assert_called_once_with(
            "https://example.com/hook", "whsec_c2VjcmV0", str(delivery.event_id), '{"type": "observation.created"}'
        )

    def test_retryable_failure_backs_off_and_stops(self):
        self.mock_send.return_value = _result(503)
        first = self._delivery()
        second = self._delivery()

        self._deliver()

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.PENDING, first.status)
        self.assertEqual(1, first.attempts)
        self.assertEqual(503, first.response_status_code)
        self.assertEqual("HTTP 503", first.error)
        self.assertEqual(0, second.attempts)
        self.mock_send.assert_called_once()
        self.assertEqual(1, self.webhook.consecutive_failures)
        self.assertEqual(NOW + timedelta(seconds=60), self.webhook.next_attempt_at)

    def test_backoff_grows_and_caps(self):
        self.mock_send.return_value = _result(503)
        self._delivery()

        for consecutive_failures, backoff in ((3, 7200), (9, 21600)):
            with self.subTest(consecutive_failures=consecutive_failures):
                self._set_webhook(consecutive_failures=consecutive_failures, next_attempt_at=None)

                self._deliver()

                self.assertEqual(consecutive_failures + 1, self.webhook.consecutive_failures)
                self.assertEqual(NOW + timedelta(seconds=backoff), self.webhook.next_attempt_at)

    def test_last_attempt_fails_delivery(self):
        self.mock_send.return_value = _result(503)
        delivery = self._delivery(attempts=5)

        self._deliver()

        delivery.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.FAILED, delivery.status)
        self.assertEqual(6, delivery.attempts)

    def test_permanent_failure_fails_and_continues(self):
        self.mock_send.side_effect = [_result(400), _result(200)]
        first = self._delivery()
        second = self._delivery()

        self._deliver()

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.FAILED, first.status)
        self.assertEqual("HTTP 400", first.error)
        self.assertEqual(Webhook_Delivery_Status.SUCCEEDED, second.status)
        self.assertEqual(0, self.webhook.consecutive_failures)
        self.assertIsNone(self.webhook.next_attempt_at)

    def test_permanent_failures_stop_at_threshold(self):
        self.mock_send.return_value = _result(404)
        deliveries = [self._delivery() for _ in range(6)]

        self._deliver()

        statuses = list(
            Webhook_Delivery.objects.filter(pk__in=[d.pk for d in deliveries])
            .order_by("pk")
            .values_list("status", "attempts")
        )
        self.assertEqual([(Webhook_Delivery_Status.FAILED, 1)] * 5 + [(Webhook_Delivery_Status.PENDING, 0)], statuses)
        self.assertEqual(5, self.webhook.consecutive_failures)
        self.assertEqual(NOW + timedelta(seconds=21600), self.webhook.next_attempt_at)

    def test_unexpired_lease_blocks(self):
        self._set_webhook(next_attempt_at=NOW + timedelta(seconds=30))
        self._delivery()

        self._deliver()

        self.mock_send.assert_not_called()
        self.assertEqual(NOW + timedelta(seconds=30), self.webhook.next_attempt_at)

    def test_expired_lease_is_reclaimed(self):
        self._set_webhook(next_attempt_at=NOW - timedelta(seconds=1))
        delivery = self._delivery()

        self._deliver()

        delivery.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.SUCCEEDED, delivery.status)
        self.assertIsNone(self.webhook.next_attempt_at)

    def test_inactive_webhook_not_sent(self):
        self._set_webhook(active=False)
        self._delivery()

        self._deliver()

        self.mock_send.assert_not_called()
        self.assertIsNone(self.webhook.next_attempt_at)

    def test_lost_lease_stops_the_drain(self):
        first = self._delivery()
        second = self._delivery()

        def send_and_lose_lease(*args):
            # A reset of the webhook while the request is in flight
            self._set_webhook(next_attempt_at=None)
            return _result(200)

        self.mock_send.side_effect = send_and_lose_lease

        self._deliver()

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.SUCCEEDED, first.status)
        self.assertEqual(Webhook_Delivery_Status.PENDING, second.status)
        self.mock_send.assert_called_once()

    def test_lease_follows_timeout(self):
        leases = []

        def send_and_capture_lease(*args):
            leases.append(Webhook.objects.get(pk=self.webhook.pk).next_attempt_at)
            return _result(200)

        self.mock_send.side_effect = send_and_capture_lease
        self._delivery()

        self._deliver()
        with override_settings(WEBHOOK_TIMEOUT=40):
            self._delivery()
            self._delivery()
            self._deliver()

        # The claim with the default timeout, then the claim and the renewal with 40 s
        self.assertEqual(
            [NOW + timedelta(seconds=60), NOW + timedelta(seconds=120), NOW + timedelta(seconds=120)], leases
        )

    def test_unexpected_exception_is_reported_and_reraised(self):
        mock_handle_task_exception = self._patch("handle_task_exception")
        error = RuntimeError("boom")
        self.mock_send.side_effect = error
        self._delivery()

        with self.assertRaises(RuntimeError):
            deliver_webhook.call_local(self.webhook.pk)

        mock_handle_task_exception.assert_called_once_with(error)

    def test_alert_once_at_threshold(self):
        self.mock_send.return_value = _result(503)
        self._delivery()

        for consecutive_failures, alerts in ((4, 1), (5, 0)):
            with self.subTest(consecutive_failures=consecutive_failures):
                self.mock_alert.reset_mock()
                self._set_webhook(consecutive_failures=consecutive_failures, next_attempt_at=None)

                self._deliver()

                self.assertEqual(alerts, self.mock_alert.call_count)
                if alerts:
                    self.assertIsInstance(self.mock_alert.call_args.kwargs["exception"], WebhookDeliveryError)
                    self.assertEqual("deliver_webhook", self.mock_alert.call_args.kwargs["function"])

    def test_batch_then_reschedule(self):
        Webhook_Delivery.objects.bulk_create(
            Webhook_Delivery(
                webhook=self.webhook, event_id=uuid.uuid4(), event_type="observation.created", payload="{}"
            )
            for _ in range(101)
        )

        self._deliver()

        self.assertEqual(100, self.mock_send.call_count)
        self.assertEqual(1, Webhook_Delivery.objects.filter(status=Webhook_Delivery_Status.PENDING).count())
        self.assertIsNone(self.webhook.next_attempt_at)
        self.mock_schedule.assert_called_once_with(args=(self.webhook.pk,), delay=0)

    def test_kick_coalesces(self):
        kick_webhooks([self.webhook.pk])
        kick_webhooks([self.webhook.pk])

        self.webhook.refresh_from_db()
        self.assertEqual(NOW + timedelta(seconds=2), self.webhook.next_attempt_at)
        self.mock_schedule.assert_called_once_with(args=(self.webhook.pk,), delay=2)

    def test_kick_after_expired_value(self):
        self._set_webhook(next_attempt_at=NOW - timedelta(seconds=1))

        kick_webhooks([self.webhook.pk])

        self.mock_schedule.assert_called_once_with(args=(self.webhook.pk,), delay=2)

    def test_kick_skips_backoff_and_inactive(self):
        self._set_webhook(next_attempt_at=NOW + timedelta(seconds=60))
        inactive = self._webhook(active=False)

        kick_webhooks([self.webhook.pk, inactive.pk])

        self.mock_schedule.assert_not_called()
        inactive.refresh_from_db()
        self.assertIsNone(inactive.next_attempt_at)

    def test_dispatch_schedules_due_only(self):
        self._delivery()
        past = self._webhook(next_attempt_at=NOW - timedelta(seconds=1))
        self._delivery(webhook=past)
        in_backoff = self._webhook(next_attempt_at=NOW + timedelta(seconds=60))
        self._delivery(webhook=in_backoff)
        without_pending = self._webhook()
        self._delivery(webhook=without_pending, status=Webhook_Delivery_Status.SUCCEEDED)
        inactive = self._webhook(active=False)
        self._delivery(webhook=inactive)

        dispatch_webhooks()

        self.assertCountEqual(
            [call(args=(self.webhook.pk,), delay=0), call(args=(past.pk,), delay=0)],
            self.mock_schedule.call_args_list,
        )
