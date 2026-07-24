from unittest.mock import patch

from django.core.management import call_command

from application.access_control.queries.user import (
    get_user_by_username,
    get_users,
)
from unittests.base_test_case import BaseTestCase


class TestQueries(BaseTestCase):
    patch.TEST_PREFIX = (
        "test",
        "setUp",
    )

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(self, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def test_get_user_by_username_not_found(self):
        self.assertIsNone(get_user_by_username("not_found"))

    def test_get_user_by_username_success(self):
        user = get_user_by_username("db_admin")
        self.assertEqual("db_admin", user.full_name)
        self.assertTrue(user.is_superuser)

    @patch("application.access_control.queries.user.get_current_user")
    def test_getusers_none(self, mock_user):
        mock_user.return_value = None

        self.assertEqual(0, len(get_users()))
        mock_user.assert_called_once()
