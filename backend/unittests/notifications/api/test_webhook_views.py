import json
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Product
from application.notifications.api.views import WebhookViewSet
from application.notifications.models import Webhook, Webhook_Delivery
from application.notifications.services.webhook_send import Webhook_Send_Result
from application.notifications.types import Webhook_Delivery_Status
from unittests.base_test_case import BaseTestCase


class TestWebhookViews(BaseTestCase):
    def setUp(self):
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        patcher = patch(
            "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        )
        self.addCleanup(patcher.stop)
        self.mock_authentication = patcher.start()
        self._login("db_admin")
        self.api_client = APIClient()
        self.webhook = self._webhook(Product.objects.get(pk=1))

    def _login(self, username: str) -> None:
        self.mock_authentication.return_value = User.objects.get(username=username), None

    def _webhook(self, product, **kwargs) -> Webhook:
        return Webhook.objects.create(
            product=product,
            name="hook",
            url="https://example.com/hook",
            secret="whsec_c2VjcmV0",
            event_types="observation.created",
            **kwargs,
        )

    def _delivery(self, webhook: Webhook, **kwargs) -> Webhook_Delivery:
        fields = {"event_id": uuid.uuid4(), "event_type": "observation.created", "payload": "{}"} | kwargs
        return Webhook_Delivery.objects.create(webhook=webhook, **fields)

    def _create(self, **data):
        post_data = {"product": 1, "name": "new", "url": "https://example.com/new", "event_types": ["import.completed"]}
        post_data.update(data)
        return self.api_client.post("/api/webhooks/", post_data, format="json")

    def _ids(self, url: str) -> set[int]:
        response = self.api_client.get(url)
        self.assertEqual(200, response.status_code)
        return {row["id"] for row in response.data["results"]}

    def test_secret_only_in_create_and_rotate(self):
        response = self._create(event_types=["observation.created", "import.completed"], secret="whsec_chosen")

        self.assertEqual(201, response.status_code)
        webhook = Webhook.objects.get(pk=response.data["id"])
        self.assertTrue(response.data["secret"].startswith("whsec_"))
        self.assertEqual(webhook.secret, response.data["secret"])
        self.assertNotEqual("whsec_chosen", webhook.secret)
        self.assertEqual(["observation.created", "import.completed"], response.data["event_types"])
        self.assertEqual("observation.created,import.completed", webhook.event_types)

        self._delivery(webhook)
        for url in (
            "/api/webhooks/",
            f"/api/webhooks/{webhook.pk}/",
            "/api/webhook_deliveries/",
        ):
            response = self.api_client.get(url)
            self.assertEqual(200, response.status_code)
            self.assertNotIn("secret", json.dumps(response.data, default=str))
            self.assertNotIn(webhook.secret, json.dumps(response.data, default=str))

        old_secret = webhook.secret
        response = self.api_client.post(f"/api/webhooks/{webhook.pk}/rotate_secret/")

        self.assertEqual(200, response.status_code)
        webhook.refresh_from_db()
        self.assertEqual({"secret": webhook.secret}, response.data)
        self.assertTrue(webhook.secret.startswith("whsec_"))
        self.assertNotEqual(old_secret, webhook.secret)

    def test_rejects_unknown_or_test_event_type(self):
        for event_types in (["unknown"], ["webhook.test"], ["import.completed", "unknown"]):
            response = self._create(event_types=event_types)
            self.assertEqual(400, response.status_code, event_types)
        self.assertEqual(1, Webhook.objects.count())

    def test_rejects_non_http_url(self):
        for url in (
            "ftp://example.com/hook",
            "example.com/hook",
            "https://",
            "https://[::1/hook",
            "javascript:alert(1)",
        ):
            response = self._create(url=url)
            self.assertEqual(400, response.status_code, url)

        response = self.api_client.patch(
            f"/api/webhooks/{self.webhook.pk}/", {"url": "file:///etc/passwd"}, format="json"
        )
        self.assertEqual(400, response.status_code)

    def test_accepts_http_url_with_single_label_host(self):
        response = self._create(url="http://receiver:8080/hook")

        self.assertEqual(201, response.status_code)

    def test_requires_event_type(self):
        self.assertEqual(400, self._create(event_types=[]).status_code)

        response = self.api_client.post(
            "/api/webhooks/", {"product": 1, "name": "new", "url": "https://example.com/new"}, format="json"
        )
        self.assertEqual(400, response.status_code)

    def test_product_cannot_change(self):
        url = f"/api/webhooks/{self.webhook.pk}/"
        for product in (2, 3, None):
            response = self.api_client.patch(url, {"product": product}, format="json")
            self.assertEqual(400, response.status_code, product)
        self.webhook.refresh_from_db()
        self.assertEqual(1, self.webhook.product_id)

        global_webhook = self._webhook(None)
        response = self.api_client.patch(f"/api/webhooks/{global_webhook.pk}/", {"product": 1}, format="json")
        self.assertEqual(400, response.status_code)

        response = self.api_client.patch(url, {"product": 1, "name": "renamed"}, format="json")
        self.assertEqual(200, response.status_code)

    def _engine_writes_after_load(self):
        """Simulates the delivery engine writing its columns between the view's load and save."""
        get_object = WebhookViewSet.get_object

        def get_object_then_engine_writes(view):
            webhook = get_object(view)
            Webhook.objects.filter(pk=webhook.pk).update(consecutive_failures=3)
            return webhook

        return patch.object(WebhookViewSet, "get_object", get_object_then_engine_writes)

    def test_update_breaks_lease_and_keeps_engine_columns(self):
        Webhook.objects.filter(pk=self.webhook.pk).update(next_attempt_at=timezone.now() + timedelta(hours=1))

        with self._engine_writes_after_load():
            response = self.api_client.patch(
                f"/api/webhooks/{self.webhook.pk}/",
                {"name": "renamed", "event_types": ["import.completed"], "consecutive_failures": 0},
                format="json",
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual(["import.completed"], response.data["event_types"])
        self.webhook.refresh_from_db()
        self.assertEqual("renamed", self.webhook.name)
        self.assertEqual("import.completed", self.webhook.event_types)
        self.assertEqual("whsec_c2VjcmV0", self.webhook.secret)
        self.assertIsNone(self.webhook.next_attempt_at)
        self.assertEqual(3, self.webhook.consecutive_failures)

    def test_rotate_secret_breaks_lease_and_keeps_engine_columns(self):
        Webhook.objects.filter(pk=self.webhook.pk).update(next_attempt_at=timezone.now() + timedelta(hours=1))

        with self._engine_writes_after_load():
            response = self.api_client.post(f"/api/webhooks/{self.webhook.pk}/rotate_secret/")

        self.assertEqual(200, response.status_code)
        self.webhook.refresh_from_db()
        self.assertEqual(response.data["secret"], self.webhook.secret)
        self.assertIsNone(self.webhook.next_attempt_at)
        self.assertEqual(3, self.webhook.consecutive_failures)

    def test_send_test_success_resets_backoff(self):
        backoff = timezone.now() + timedelta(hours=1)
        Webhook.objects.filter(pk=self.webhook.pk).update(consecutive_failures=4, next_attempt_at=backoff)

        with patch(
            "application.notifications.api.views.send_webhook_request", return_value=Webhook_Send_Result(204, "")
        ) as mock_send:
            response = self.api_client.post(f"/api/webhooks/{self.webhook.pk}/send_test/")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"succeeded": True, "status_code": 204, "error": ""}, response.data)
        self.webhook.refresh_from_db()
        self.assertEqual(0, self.webhook.consecutive_failures)
        self.assertIsNone(self.webhook.next_attempt_at)
        url, secret, message_id, body = mock_send.call_args.args
        self.assertEqual(("https://example.com/hook", "whsec_c2VjcmV0"), (url, secret))
        uuid.UUID(message_id)
        payload = json.loads(body)
        self.assertEqual("webhook.test", payload["type"])
        self.assertEqual({"webhook": {"id": self.webhook.pk, "name": "hook"}}, payload["data"])
        self.assertFalse(Webhook_Delivery.objects.exists())

    def test_changed_by_follows_create_update_and_rotate(self):
        admin = User.objects.get(username="db_admin")
        response = self._create()
        self.assertEqual(201, response.status_code)
        webhook = Webhook.objects.get(pk=response.data["id"])
        self.assertEqual(admin, webhook.user)
        self.assertEqual(admin.full_name, response.data["user_full_name"])

        other = User.objects.create(username="other_admin", first_name="Other", last_name="Admin", is_superuser=True)
        self._login("other_admin")
        response = self.api_client.patch(f"/api/webhooks/{webhook.pk}/", {"name": "renamed"}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertEqual("Other Admin", response.data["user_full_name"])
        webhook.refresh_from_db()
        self.assertEqual(other, webhook.user)

        Webhook.objects.filter(pk=webhook.pk).update(user=admin)
        response = self.api_client.post(f"/api/webhooks/{webhook.pk}/rotate_secret/")
        self.assertEqual(200, response.status_code)
        webhook.refresh_from_db()
        self.assertEqual(other, webhook.user)

    def test_send_test_keeps_changed_by(self):
        admin = User.objects.get(username="db_admin")
        Webhook.objects.filter(pk=self.webhook.pk).update(user=admin)
        User.objects.create(username="other_admin", is_superuser=True)
        self._login("other_admin")

        with patch(
            "application.notifications.api.views.send_webhook_request", return_value=Webhook_Send_Result(204, "")
        ):
            response = self.api_client.post(f"/api/webhooks/{self.webhook.pk}/send_test/")

        self.assertEqual(200, response.status_code)
        self.webhook.refresh_from_db()
        self.assertEqual(admin, self.webhook.user)

    def test_deleting_the_user_keeps_the_webhook(self):
        user = User.objects.create(username="leaving")
        Webhook.objects.filter(pk=self.webhook.pk).update(user=user)

        user.delete()

        self.webhook.refresh_from_db()
        self.assertIsNone(self.webhook.user)
        response = self.api_client.get(f"/api/webhooks/{self.webhook.pk}/")
        self.assertIsNone(response.data["user_full_name"])

    def test_send_test_failure_changes_nothing(self):
        backoff = timezone.now() + timedelta(hours=1)
        Webhook.objects.filter(pk=self.webhook.pk).update(consecutive_failures=4, next_attempt_at=backoff)

        with patch(
            "application.notifications.api.views.send_webhook_request",
            return_value=Webhook_Send_Result(503, "HTTP 503: down"),
        ):
            response = self.api_client.post(f"/api/webhooks/{self.webhook.pk}/send_test/")

        self.assertEqual(200, response.status_code)
        self.assertEqual({"succeeded": False, "status_code": 503, "error": "HTTP 503: down"}, response.data)
        self.webhook.refresh_from_db()
        self.assertEqual(4, self.webhook.consecutive_failures)
        self.assertEqual(backoff, self.webhook.next_attempt_at)

    def test_send_test_without_response(self):
        with patch(
            "application.notifications.api.views.send_webhook_request",
            return_value=Webhook_Send_Result(None, "URL rejected, see the backend log"),
        ):
            response = self.api_client.post(f"/api/webhooks/{self.webhook.pk}/send_test/")

        self.assertEqual(
            {"succeeded": False, "status_code": None, "error": "URL rejected, see the backend log"}, response.data
        )

    def test_redeliver_resets_delivery(self):
        delivery = self._delivery(
            self.webhook,
            status=Webhook_Delivery_Status.FAILED,
            attempts=6,
            error="HTTP 500: boom",
            response_status_code=500,
        )

        with (
            patch("application.notifications.api.views.kick_webhooks") as mock_kick,
            self.captureOnCommitCallbacks(execute=True),
        ):
            response = self.api_client.post(f"/api/webhook_deliveries/{delivery.pk}/redeliver/")

        self.assertEqual(204, response.status_code)
        delivery.refresh_from_db()
        self.assertEqual(Webhook_Delivery_Status.PENDING, delivery.status)
        self.assertEqual(0, delivery.attempts)
        self.assertEqual("", delivery.error)
        self.assertIsNone(delivery.response_status_code)
        mock_kick.assert_called_once_with([self.webhook.pk])

    def test_queryset_scoped_to_membership(self):
        product_2_webhook = self._webhook(Product.objects.get(pk=2))
        group_webhook = self._webhook(Product.objects.get(pk=3))
        admin_group_webhook = self._webhook(Product.objects.get(pk=4))
        global_webhook = self._webhook(None)
        deliveries = {
            webhook.pk: self._delivery(webhook).pk
            for webhook in (self.webhook, product_2_webhook, group_webhook, admin_group_webhook, global_webhook)
        }

        expected = {
            "db_admin": {
                self.webhook.pk,
                product_2_webhook.pk,
                group_webhook.pk,
                admin_group_webhook.pk,
                global_webhook.pk,
            },
            "db_product_group_user": {self.webhook.pk, group_webhook.pk},
            "db_internal_write": {self.webhook.pk},
            "db_internal_read": {self.webhook.pk, product_2_webhook.pk},
            "db_external": {product_2_webhook.pk},
        }
        for username, webhook_ids in expected.items():
            self._login(username)
            self.assertEqual(webhook_ids, self._ids("/api/webhooks/"), username)
            self.assertEqual(
                {deliveries[webhook_id] for webhook_id in webhook_ids},
                self._ids("/api/webhook_deliveries/"),
                username,
            )

    def test_filters(self):
        inactive_webhook = self._webhook(Product.objects.get(pk=2), active=False)
        failed = self._delivery(self.webhook, status=Webhook_Delivery_Status.FAILED)
        pending = self._delivery(self.webhook, event_type="import.completed")
        other = self._delivery(inactive_webhook)

        self.assertEqual({self.webhook.pk}, self._ids("/api/webhooks/?product=1"))
        self.assertEqual({inactive_webhook.pk}, self._ids("/api/webhooks/?active=false"))
        self.assertEqual({failed.pk, pending.pk}, self._ids(f"/api/webhook_deliveries/?webhook={self.webhook.pk}"))
        self.assertEqual({failed.pk}, self._ids("/api/webhook_deliveries/?status=Failed"))
        self.assertEqual({pending.pk}, self._ids("/api/webhook_deliveries/?event_type=import.completed"))

        response = self.api_client.get("/api/webhook_deliveries/")
        self.assertEqual([other.pk, pending.pk, failed.pk], [row["id"] for row in response.data["results"]])
