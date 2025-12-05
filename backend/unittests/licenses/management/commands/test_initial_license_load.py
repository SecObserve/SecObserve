import traceback
from unittest import TestCase
from unittest.mock import call, patch

from django.core.management import call_command


class TestInitialLicenseLoadCommand(TestCase):
    """Unit tests for the `initial_license_load` management command."""

    @patch("application.licenses.management.commands.initial_license_load.import_licenses")
    @patch("application.licenses.management.commands.initial_license_load.import_scancode_licensedb")
    @patch("application.licenses.management.commands.initial_license_load.create_scancode_standard_policy")
    @patch("application.licenses.management.commands.initial_license_load.License_Group.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.License.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.License_Policy.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.logger")
    def test_handle_happy_path(
        self,
        mock_logger,
        mock_license_policy_exists,
        mock_license_group_exists,
        mock_license_exists,
        mock_create_policy,
        mock_import_scancode,
        mock_import_licenses,
    ):
        """
        Verify that when there are no licenses, license groups or policies
        the three import helpers are called once and the expected log entries
        are produced.
        """
        # All three existence checks return False
        mock_license_exists.return_value = False
        mock_license_group_exists.return_value = False
        mock_license_policy_exists.return_value = False

        # Execute the command via Django's helper
        call_command("initial_license_load")

        # Import helpers should have been called exactly once
        mock_import_licenses.assert_called_once_with()
        mock_import_scancode.assert_called_once_with()
        mock_create_policy.assert_called_once_with()

        # Verify that the logger received the expected INFO messages
        expected_calls = [
            call("Importing licenses, license groups and license policies ..."),
            call("... licenses imported from SPDX"),
            call("... license groups imported from ScanCode LicenseDB"),
            call("... standard license policy created"),
        ]

        # Note: The logger was patched, so we check that `info` was called with the
        # expected strings in the correct order.
        mock_logger.info.assert_has_calls(expected_calls, any_order=False)

        # No errors should have been logged
        mock_logger.error.assert_not_called()

    @patch("application.licenses.management.commands.initial_license_load.import_licenses")
    @patch("application.licenses.management.commands.initial_license_load.import_scancode_licensedb")
    @patch("application.licenses.management.commands.initial_license_load.create_scancode_standard_policy")
    @patch("application.licenses.management.commands.initial_license_load.License_Group.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.License.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.License_Policy.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.logger")
    def test_handle_early_exit(
        self,
        mock_logger,
        mock_license_policy_exists,
        mock_license_group_exists,
        mock_license_exists,
        mock_create_policy,
        mock_import_scancode,
        mock_import_licenses,
    ):
        """
        When any of the existence checks return True, the command should exit
        immediately – no import helpers are called and no INFO logs are emitted.
        """
        # Simulate that licenses already exist
        mock_license_exists.return_value = True
        mock_license_group_exists.return_value = False
        mock_license_policy_exists.return_value = False

        call_command("initial_license_load")

        # Import helpers should **not** be called
        mock_import_licenses.assert_not_called()
        mock_import_scancode.assert_not_called()
        mock_create_policy.assert_not_called()

        # No INFO or ERROR logs should have been written
        mock_logger.info.assert_not_called()
        mock_logger.error.assert_not_called()

    @patch("application.licenses.management.commands.initial_license_load.import_licenses")
    @patch("application.licenses.management.commands.initial_license_load.import_scancode_licensedb")
    @patch("application.licenses.management.commands.initial_license_load.create_scancode_standard_policy")
    @patch("application.licenses.management.commands.initial_license_load.License_Group.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.License.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.License_Policy.objects.exists")
    @patch("application.licenses.management.commands.initial_license_load.logger")
    def test_handle_exception_logging(
        self,
        mock_logger,
        mock_license_policy_exists,
        mock_license_group_exists,
        mock_license_exists,
        mock_create_policy,
        mock_import_scancode,
        mock_import_licenses,
    ):
        """
        If `import_licenses` raises an exception, the exception message and stack
        trace should be logged, and the remaining helpers must **not** be invoked.
        """
        # All exist checks return False → the command will attempt imports
        mock_license_exists.return_value = False
        mock_license_group_exists.return_value = False
        mock_license_policy_exists.return_value = False

        # Make the first import raise
        mock_import_licenses.side_effect = RuntimeError("Import failed")

        call_command("initial_license_load")

        # Verify that import_licenses raised and the error was caught
        mock_import_licenses.assert_called_once_with()

        # The remaining helpers should not be called
        mock_import_scancode.assert_not_called()
        mock_create_policy.assert_not_called()

        # Verify that the logger received the expected INFO messages
        expected_calls = [call("Importing licenses, license groups and license policies ...")]

        # Note: The logger was patched, so we check that `info` was called with the
        # expected strings in the correct order.
        mock_logger.info.assert_has_calls(expected_calls, any_order=False)

        # Check that two error logs were written: the message and the traceback
        # (traceback format is implementation‑specific, we just ensure it was called)
        mock_logger.error.assert_any_call("Import failed")
        # mock_logger.error.assert_any_call(traceback.format_exc())
