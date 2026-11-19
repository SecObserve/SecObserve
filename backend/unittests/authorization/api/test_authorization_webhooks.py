import uuid
from unittest.mock import patch

from application.core.models import Product
from application.notifications.models import Webhook, Webhook_Delivery
from application.notifications.services.webhook_send import Webhook_Send_Result
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)

NO_PERMISSION = "{'message': 'You do not have permission to perform this action.'}"
NO_WEBHOOK = "{'message': 'No Webhook matches the given query.'}"
NO_DELIVERY = "{'message': 'No Webhook_Delivery matches the given query.'}"


def _webhook(product_id) -> Webhook:
    return Webhook.objects.create(
        product=Product.objects.get(pk=product_id) if product_id else None,
        name=f"webhook {product_id}",
        url="https://example.com/hook",
        secret="whsec_c2VjcmV0",
        event_types="observation.created",
    )


def _delivery(webhook: Webhook) -> Webhook_Delivery:
    return Webhook_Delivery.objects.create(
        webhook=webhook, event_id=uuid.uuid4(), event_type="observation.created", payload="{}", status="Failed"
    )


class TestAuthorizationWebhooks(TestAuthorizationBase):
    def test_authorization_webhooks_product_member(self):
        self._test_authorization_webhooks()

    def test_authorization_webhooks_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_webhooks()

    @patch("application.notifications.api.views.kick_webhooks")
    @patch("application.notifications.api.views.send_webhook_request", return_value=Webhook_Send_Result(204, ""))
    def _test_authorization_webhooks(self, mock_send, mock_kick):
        product_1 = _webhook(1)
        product_2 = _webhook(2)
        group = _webhook(3)
        global_webhook = _webhook(None)
        delivery_1 = _delivery(product_1)
        delivery_2 = _delivery(product_2)
        delivery_global = _delivery(global_webhook)

        webhooks = "/api/webhooks/"
        deliveries = "/api/webhook_deliveries/"
        post_data = {"name": "new", "url": "https://example.com/new", "event_types": ["import.completed"]}

        # Read
        self._test_api(APITest("db_admin", "get", webhooks, None, 200, None))
        self._test_api(APITest("db_admin", "get", f"{webhooks}{global_webhook.pk}/", None, 200, None))
        self._test_api(APITest("db_internal_write", "get", f"{webhooks}{product_1.pk}/", None, 200, None))
        self._test_api(
            APITest("db_internal_read", "get", f"{webhooks}{product_1.pk}/", None, 200, None, no_second_user=True)
        )
        self._test_api(APITest("db_internal_write", "get", f"{webhooks}{product_2.pk}/", None, 404, NO_WEBHOOK))
        self._test_api(APITest("db_internal_write", "get", f"{webhooks}{global_webhook.pk}/", None, 404, NO_WEBHOOK))
        self._test_api(APITest("db_internal_write", "get", f"{webhooks}{group.pk}/", None, 404, NO_WEBHOOK, True))
        self._test_api(APITest("db_product_group_user", "get", f"{webhooks}{group.pk}/", None, 200, None))
        self._test_api(APITest("db_external", "get", f"{webhooks}{product_1.pk}/", None, 404, NO_WEBHOOK))
        self._test_api(APITest("db_internal_read", "get", f"{deliveries}{delivery_1.pk}/", None, 200, None, True))
        self._test_api(APITest("db_internal_write", "get", f"{deliveries}{delivery_2.pk}/", None, 404, NO_DELIVERY))
        self._test_api(
            APITest("db_internal_write", "get", f"{deliveries}{delivery_global.pk}/", None, 404, NO_DELIVERY)
        )

        # Create
        self._test_api(APITest("db_internal_read", "post", webhooks, post_data | {"product": 1}, 403, NO_PERMISSION))
        self._test_api(APITest("db_internal_write", "post", webhooks, post_data | {"product": 1}, 201, None))
        self._test_api(APITest("db_internal_write", "post", webhooks, post_data | {"product": 2}, 403, NO_PERMISSION))
        self._test_api(APITest("db_internal_write", "post", webhooks, post_data | {"product": 3}, 403, NO_PERMISSION))
        self._test_api(APITest("db_product_group_user", "post", webhooks, post_data | {"product": 3}, 201, None))
        self._test_api(
            APITest("db_internal_write", "post", webhooks, post_data | {"product": None}, 403, NO_PERMISSION)
        )
        self._test_api(APITest("db_internal_write", "post", webhooks, post_data | {"product": ""}, 403, NO_PERMISSION))
        self._test_api(APITest("db_internal_write", "post", webhooks, post_data, 403, NO_PERMISSION))
        self._test_api(APITest("db_admin", "post", webhooks, post_data, 201, None))

        # Change and actions
        url = f"{webhooks}{product_1.pk}/"
        for action in ("send_test", "rotate_secret"):
            self._test_api(APITest("db_internal_read", "post", f"{url}{action}/", None, 403, NO_PERMISSION))
            self._test_api(APITest("db_external", "post", f"{url}{action}/", None, 404, NO_WEBHOOK))
            self._test_api(APITest("db_internal_write", "post", f"{url}{action}/", None, 200, None))
            self._test_api(
                APITest("db_internal_write", "post", f"{webhooks}{global_webhook.pk}/{action}/", None, 404, NO_WEBHOOK)
            )
            self._test_api(APITest("db_admin", "post", f"{webhooks}{global_webhook.pk}/{action}/", None, 200, None))
        self._test_api(APITest("db_internal_read", "patch", url, {"name": "changed"}, 403, NO_PERMISSION))
        self._test_api(APITest("db_internal_write", "patch", url, {"name": "changed"}, 200, None))
        self._test_api(
            APITest("db_internal_write", "patch", f"{webhooks}{product_2.pk}/", {"name": "x"}, 404, NO_WEBHOOK)
        )
        self._test_api(APITest("db_admin", "patch", f"{webhooks}{global_webhook.pk}/", {"name": "x"}, 200, None))

        redeliver = f"{deliveries}{delivery_1.pk}/redeliver/"
        self._test_api(APITest("db_internal_read", "post", redeliver, None, 403, NO_PERMISSION))
        self._test_api(APITest("db_external", "post", redeliver, None, 404, NO_DELIVERY))
        self._test_api(APITest("db_internal_write", "post", redeliver, None, 204, None))
        self._test_api(
            APITest("db_internal_write", "post", f"{deliveries}{delivery_global.pk}/redeliver/", None, 404, NO_DELIVERY)
        )
        self._test_api(APITest("db_admin", "post", f"{deliveries}{delivery_global.pk}/redeliver/", None, 204, None))

        # Delete
        self._test_api(APITest("db_internal_read", "delete", url, None, 403, NO_PERMISSION))
        self._test_api(APITest("db_internal_write", "delete", f"{webhooks}{group.pk}/", None, 404, NO_WEBHOOK))
        self._test_api(APITest("db_internal_write", "delete", url, None, 204, None))
        self._test_api(APITest("db_admin", "delete", f"{webhooks}{global_webhook.pk}/", None, 204, None))
