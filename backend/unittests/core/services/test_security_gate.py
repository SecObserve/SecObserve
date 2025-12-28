from unittest.mock import patch

from application.commons.models import Settings
from application.core.models import Product
from application.core.services.security_gate import (
    check_security_gate,
    check_security_gate_observation,
)
from unittests.base_test_case import BaseTestCase


class TestSecurityGate(BaseTestCase):
    @patch("application.core.models.Product.save")
    @patch("application.core.services.security_gate.send_product_security_gate_notification")
    def test_check_security_gate_unchanged(self, notification_mock, save_mock):
        product = Product(security_gate_passed=None, security_gate_active=False)

        check_security_gate(product)

        self.assertIsNone(product.security_gate_passed)
        save_mock.assert_not_called()
        notification_mock.assert_not_called()

    @patch("application.core.models.Product.save")
    @patch("application.core.services.security_gate.send_product_security_gate_notification")
    def test_check_security_gate_false_and_changed(self, notification_mock, save_mock):
        product = Product(security_gate_passed=True, security_gate_active=False)

        check_security_gate(product)

        self.assertIsNone(product.security_gate_passed)
        save_mock.assert_called()
        notification_mock.assert_called_with(product)

    @patch("application.core.models.Product.save")
    @patch("application.core.services.security_gate.send_product_security_gate_notification")
    def test_check_security_gate_false_and_changed_product_group(self, notification_mock, save_mock):
        product_group = Product(is_product_group=True, security_gate_active=False)
        product = Product(
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=True,
        )

        check_security_gate(product)

        self.assertIsNone(product.security_gate_passed)
        save_mock.assert_called()
        notification_mock.assert_called_with(product)

    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_true_critical(self, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=False,
            security_gate_active=True,
            security_gate_threshold_critical=1,
        )
        product.open_critical_observation_count = 2
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    @patch("application.notifications.models.Notification.save")
    def test_check_security_gate_true_critical_product_group(
        self, notification_save_mock, product_save_mock, get_product_mock
    ):
        product_group = Product(
            is_product_group=True,
            security_gate_active=True,
            security_gate_threshold_critical=1,
        )
        product = Product(
            id=999,
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=False,
        )
        product.open_critical_observation_count = 2
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_called()
        notification_save_mock.assert_called()

    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_true_high(self, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=False,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=1,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 2
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    @patch("application.notifications.models.Notification.save")
    def test_check_security_gate_true_high_product_group(
        self, notification_save_mock, product_save_mock, get_product_mock
    ):
        product_group = Product(
            is_product_group=True,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=1,
        )
        product = Product(
            id=999,
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 2
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_called()
        notification_save_mock.assert_called()

    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_true_medium(self, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=False,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=1,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 2
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    @patch("application.notifications.models.Notification.save")
    def test_check_security_gate_true_medium_product_group(
        self, notification_save_mock, product_save_mock, get_product_mock
    ):
        product_group = Product(
            is_product_group=True,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=1,
        )
        product = Product(
            id=999,
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 2
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_called()
        notification_save_mock.assert_called()

    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_true_low(self, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=False,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=1,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 2
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    @patch("application.notifications.models.Notification.save")
    def test_check_security_gate_true_low_product_group(
        self, notification_save_mock, product_save_mock, get_product_mock
    ):
        product_group = Product(
            id=999,
            is_product_group=True,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=1,
        )
        product = Product(
            id=999,
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 2
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_called()
        notification_save_mock.assert_called()

    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_true_none(self, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=False,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=3,
            security_gate_threshold_none=1,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 2
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    @patch("application.notifications.models.Notification.save")
    def test_check_security_gate_true_none_product_group(
        self, notification_save_mock, product_save_mock, get_product_mock
    ):
        product_group = Product(
            is_product_group=True,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=3,
            security_gate_threshold_none=1,
        )
        product = Product(
            id=999,
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 2
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_called()
        notification_save_mock.assert_called()

    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_true_unknown(self, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=False,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=3,
            security_gate_threshold_none=3,
            security_gate_threshold_unknown=1,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 2

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    @patch("application.notifications.models.Notification.save")
    def test_check_security_gate_true_unknown_product_group(
        self, notification_save_mock, product_save_mock, get_product_mock
    ):
        product_group = Product(
            is_product_group=True,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=3,
            security_gate_threshold_none=3,
            security_gate_threshold_unknown=1,
        )
        product = Product(
            id=999,
            product_group=product_group,
            security_gate_passed=True,
            security_gate_active=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 2

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_called()
        notification_save_mock.assert_called()

    @patch("application.core.services.security_gate.get_product_by_id")
    @patch("application.core.models.Product.save")
    def test_check_security_gate_true_no_match(self, product_save_mock, get_product_mock):
        product = Product(
            id=999,
            security_gate_passed=True,
            security_gate_active=True,
            security_gate_threshold_critical=3,
            security_gate_threshold_high=3,
            security_gate_threshold_medium=3,
            security_gate_threshold_low=3,
            security_gate_threshold_none=3,
            security_gate_threshold_unknown=3,
        )
        product.open_critical_observation_count = 2
        product.open_high_observation_count = 2
        product.open_medium_observation_count = 2
        product.open_low_observation_count = 2
        product.open_none_observation_count = 2
        product.open_unknown_observation_count = 2

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertTrue(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)
        product_save_mock.assert_not_called()

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_critical(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 1
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=False,
        )
        product.open_critical_observation_count = 2
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_high(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 3
        settings.security_gate_threshold_high = 1
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 2
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_medium(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 3
        settings.security_gate_threshold_high = 3
        settings.security_gate_threshold_medium = 1
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 2
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_low(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 3
        settings.security_gate_threshold_high = 3
        settings.security_gate_threshold_medium = 3
        settings.security_gate_threshold_low = 1
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 2
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_none(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 3
        settings.security_gate_threshold_high = 3
        settings.security_gate_threshold_medium = 3
        settings.security_gate_threshold_low = 3
        settings.security_gate_threshold_none = 1
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 2
        product.open_unknown_observation_count = 0

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_unknown(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 3
        settings.security_gate_threshold_high = 3
        settings.security_gate_threshold_medium = 3
        settings.security_gate_threshold_low = 3
        settings.security_gate_threshold_none = 3
        settings.security_gate_threshold_unknown = 1
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=False,
        )
        product.open_critical_observation_count = 0
        product.open_high_observation_count = 0
        product.open_medium_observation_count = 0
        product.open_low_observation_count = 0
        product.open_none_observation_count = 0
        product.open_unknown_observation_count = 2

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertFalse(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.commons.models.Settings.load")
    @patch("application.core.services.security_gate.get_product_by_id")
    def test_check_security_gate_none_no_match(self, get_product_mock, mock_settings_load):
        settings = Settings()
        settings.security_gate_threshold_critical = 3
        settings.security_gate_threshold_high = 3
        settings.security_gate_threshold_medium = 3
        settings.security_gate_threshold_low = 3
        settings.security_gate_threshold_none = 3
        settings.security_gate_threshold_unknown = 3
        mock_settings_load.return_value = settings

        product = Product(
            id=999,
            security_gate_passed=True,
        )
        product.open_critical_observation_count = 2
        product.open_high_observation_count = 2
        product.open_medium_observation_count = 2
        product.open_low_observation_count = 2
        product.open_none_observation_count = 2
        product.open_unknown_observation_count = 2

        get_product_mock.return_value = product

        check_security_gate(product)

        self.assertTrue(product.security_gate_passed)
        get_product_mock.assert_called_once_with(product_id=999, is_product_group=False, with_annotations=True)

    @patch("application.core.services.security_gate.check_security_gate")
    def test_check_security_gate_observation_same_branch(self, mock):
        self.product_1.repository_default_branch = self.branch_1
        self.observation_1.branch = self.branch_1

        check_security_gate_observation(self.observation_1)
        mock.assert_called_with(self.product_1)

    @patch("application.core.services.security_gate.check_security_gate")
    def test_check_security_gate_observation_no_branch(self, mock):
        self.product_1.repository_default_branch = None
        self.observation_1.branch = None

        check_security_gate_observation(self.observation_1)
        mock.assert_called_with(self.product_1)

    @patch("application.core.services.security_gate.check_security_gate")
    def test_check_security_gate_observation_different_branch(self, mock):
        self.product_1.repository_default_branch = self.branch_1
        self.observation_1.branch = self.branch_2

        check_security_gate_observation(self.observation_1)
        mock.assert_not_called()
