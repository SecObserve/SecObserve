from unittest.mock import MagicMock, patch

from application.access_control.models import User
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.notifications.services.send_notifications_product_rule_approval import (
    send_product_rule_approval_notification,
)
from application.notifications.types import Product_Notification_Type
from application.rules.types import Rule_Status
from unittests.base_test_case import BaseTestCase


class TestSendNotificationsProductRuleApproval(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.product_1.pk = 1
        self.product_rule_1.pk = 2
        self.product_rule_1.user = self.user_internal
        self.product_rule_1.approval_status = Rule_Status.RULE_STATUS_NEEDS_APPROVAL
        self.user_jane = User(
            id=10, username="jane@example.com", email="jane@example.com", first_name="Jane", full_name="Jane Doe"
        )
        self.user_john = User(id=11, username="john@example.com", email="john@example.com", full_name="John Doe")

    def _patch(self, email_from: str = "secobserve@example.com") -> dict[str, MagicMock]:
        """The mocks all tests need: the users who want the notification and their permission to
        approve rules are mocked, so that no database is needed."""
        patchers = {
            "get_users": patch(
                "application.notifications.services.send_notifications_product_rule_approval."
                "get_users_for_product_notification"
            ),
            "send_email": patch(
                "application.notifications.services.send_notifications_product_rule_approval." "send_email_notification"
            ),
            "base_url": patch(
                "application.notifications.services.send_notifications_product_rule_approval.get_base_url_frontend"
            ),
            "has_permission": patch(
                "application.notifications.services.send_notifications_product_rule_approval.user_has_permission"
            ),
            "settings_load": patch("application.commons.models.Settings.load"),
        }

        mocks = {}
        for name, patcher in patchers.items():
            mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

        settings = Settings()
        settings.email_from = email_from
        mocks["settings_load"].return_value = settings
        mocks["base_url"].return_value = "https://secobserve.com/"
        mocks["get_users"].return_value = set()
        mocks["has_permission"].return_value = True

        return mocks

    def test_send_product_rule_approval_notification_without_approval(self):
        mocks = self._patch()
        self.product_rule_1.approval_status = Rule_Status.RULE_STATUS_AUTO_APPROVED
        mocks["get_users"].return_value = {self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        mocks["get_users"].assert_not_called()
        mocks["send_email"].assert_not_called()

    def test_send_product_rule_approval_notification_for_a_general_rule(self):
        mocks = self._patch()
        self.general_rule.approval_status = Rule_Status.RULE_STATUS_NEEDS_APPROVAL
        mocks["get_users"].return_value = {self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.general_rule)

        mocks["get_users"].assert_not_called()
        mocks["send_email"].assert_not_called()

    def test_send_product_rule_approval_notification_without_email_from(self):
        mocks = self._patch(email_from="")
        mocks["get_users"].return_value = {self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        mocks["get_users"].assert_not_called()
        mocks["send_email"].assert_not_called()

    def test_send_product_rule_approval_notification_without_users(self):
        mocks = self._patch()

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        mocks["get_users"].assert_called_once_with(
            self.product_1, Product_Notification_Type.PRODUCT_RULE_TO_BE_REVIEWED
        )
        mocks["send_email"].assert_not_called()

    def test_send_product_rule_approval_notification_user_with_first_name(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        mocks["has_permission"].assert_called_once_with(
            self.product_1, Permissions.Product_Rule_Approval, self.user_jane
        )
        mocks["send_email"].assert_called_once_with(
            "jane@example.com",
            'Product rule "rule_1" needs approval',
            "email_product_rule.tpl",
            rule=self.product_rule_1,
            rule_url="https://secobserve.com/#/product_rules/2/show",
            first_line='Product rule "rule_1" needs approval',
            first_name=" Jane",
        )

    def test_send_product_rule_approval_notification_user_without_first_name(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_john}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        self.assertEqual(" John Doe", mocks["send_email"].call_args.kwargs["first_name"])

    def test_send_product_rule_approval_notification_without_approval_permission(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_jane}
        mocks["has_permission"].return_value = False

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        mocks["send_email"].assert_not_called()

    def test_send_product_rule_approval_notification_excludes_the_author(self):
        mocks = self._patch()
        # user_internal has created the rule
        mocks["get_users"].return_value = {self.user_internal, self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_rule_approval_notification(self.product_rule_1)

        mocks["send_email"].assert_called_once()
        self.assertEqual("jane@example.com", mocks["send_email"].call_args.args[0])

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_product_rule_approval.handle_task_exception")
    def test_send_product_rule_approval_notification_exception(self, mock_handle_task_exception, mock_settings_load):
        exception = Exception("test_exception")
        mock_settings_load.side_effect = exception
        self.product_rule_1.approval_status = Rule_Status.RULE_STATUS_NEEDS_APPROVAL

        # call_local calls the undecorated function, so that the exception is not swallowed
        # by Huey. It has to be re-raised, so that Huey marks the task as failed.
        with self.assertRaises(Exception) as context:
            send_product_rule_approval_notification.call_local(self.product_rule_1)
        self.assertEqual(exception, context.exception)

        mock_handle_task_exception.assert_called_once_with(exception)
