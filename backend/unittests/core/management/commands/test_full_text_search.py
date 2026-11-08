from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from application.core.services.full_text_search import FullTextSearchError
from unittests.base_test_case import BaseTestCase

COMMAND_MODULE = "application.core.management.commands.full_text_search"


class TestFullTextSearchCommand(BaseTestCase):
    @patch(f"{COMMAND_MODULE}.deactivate_full_text_search")
    @patch(f"{COMMAND_MODULE}.activate_full_text_search")
    def test_activate(self, mock_activate, mock_deactivate):
        out = StringIO()

        call_command("full_text_search", "activate", stdout=out)

        mock_activate.assert_called_once_with()
        mock_deactivate.assert_not_called()
        self.assertEqual("Full text search activated\n", out.getvalue())

    @patch(f"{COMMAND_MODULE}.deactivate_full_text_search")
    @patch(f"{COMMAND_MODULE}.activate_full_text_search")
    def test_deactivate(self, mock_activate, mock_deactivate):
        out = StringIO()

        call_command("full_text_search", "deactivate", stdout=out)

        mock_deactivate.assert_called_once_with()
        mock_activate.assert_not_called()
        self.assertEqual("Full text search deactivated\n", out.getvalue())

    def test_invalid_action(self):
        with self.assertRaises(CommandError):
            call_command("full_text_search", "invalid")

    @patch(f"{COMMAND_MODULE}.activate_full_text_search")
    def test_error(self, mock_activate):
        mock_activate.side_effect = FullTextSearchError("Full text search is only available with PostgreSQL")

        with self.assertRaises(CommandError) as e:
            call_command("full_text_search", "activate")

        self.assertEqual("Full text search is only available with PostgreSQL", str(e.exception))
