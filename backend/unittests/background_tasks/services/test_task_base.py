from unittest.mock import MagicMock, call, patch

from application.background_tasks.services.task_base import (
    _delete_older_entries,
    _handle_periodic_task_exception,
    so_periodic_task,
)
from unittests.base_test_case import BaseTestCase


class TestTaskBase(BaseTestCase):
    # ---------------------------------------------------------------
    # so_periodic_task
    # ---------------------------------------------------------------

    @patch("application.background_tasks.services.task_base.lock_task")
    @patch("application.background_tasks.services.task_base.logger")
    @patch("application.background_tasks.models.Periodic_Task.save")
    @patch("application.background_tasks.services.task_base._delete_older_entries")
    def test_so_periodic_task_successful_execution(
        self, mock_delete_older_entries, mock_save, mock_logger, mock_lock_task
    ):
        # Setup
        mock_lock_task.return_value = lambda func: func
        test_function = MagicMock()
        test_function.__name__ = "test_function"

        # Execute
        decorated_function = so_periodic_task("test_task")(test_function)
        decorated_function()

        # Assert
        mock_logger.info.assert_has_calls(
            [call("--- %s - start ---", "test_task"), call("--- %s - finished ---", "test_task")]
        )
        test_function.assert_called_once()
        self.assertEqual(mock_save.call_count, 2)
        mock_lock_task.assert_called_once_with("test_task")
        mock_delete_older_entries.assert_called_once_with("test_task")

    @patch("application.background_tasks.services.task_base._handle_periodic_task_exception")
    @patch("application.background_tasks.services.task_base.lock_task")
    @patch("application.background_tasks.services.task_base.logger")
    @patch("application.background_tasks.models.Periodic_Task.save")
    @patch("application.background_tasks.services.task_base._delete_older_entries")
    def test_so_periodic_task_exception_handling(
        self, mock_delete_older_entries, mock_save, mock_logger, mock_lock_task, mock_handle_exception
    ):
        # Setup
        mock_lock_task.return_value = lambda func: func
        test_exception = Exception("Test exception")
        test_function = MagicMock(side_effect=test_exception)
        test_function.__name__ = "test_function"

        # Execute
        decorated_function = so_periodic_task("test_task")(test_function)
        with self.assertRaises(Exception) as context:
            decorated_function()

        # Assert
        self.assertEqual(str(context.exception), "Test exception")
        mock_logger.info.assert_called_once_with("--- %s - start ---", "test_task")
        test_function.assert_called_once()
        mock_handle_exception.assert_called_once_with(test_exception)
        self.assertEqual(mock_save.call_count, 2)
        mock_delete_older_entries.assert_called_once_with("test_task")

        # Verify that the "finished" log is not called when an exception occurs
        self.assertEqual(mock_logger.info.call_count, 1)

    # ---------------------------------------------------------------
    # _handle_periodic_task_exception
    # ---------------------------------------------------------------

    @patch("application.background_tasks.services.task_base.send_task_exception_notification")
    @patch("application.background_tasks.services.task_base.format_log_message")
    @patch("application.background_tasks.services.task_base.logger")
    @patch("application.background_tasks.services.task_base.sys.exc_info")
    @patch("application.background_tasks.services.task_base.inspect.getinnerframes")
    def test_handle_periodic_task_exception_with_function_name(
        self, mock_getinnerframes, mock_exc_info, mock_logger, mock_format_log_message, mock_send_notification
    ):
        # Setup
        test_exception = Exception("Test exception")
        mock_exc_info.return_value = (None, None, "traceback_object")

        # Create a mock frame with a function attribute
        mock_frame = MagicMock()
        mock_frame.function = "test_function"
        mock_getinnerframes.return_value = [MagicMock(), mock_frame]

        mock_format_log_message.return_value = "Formatted log message"

        # Execute
        _handle_periodic_task_exception(test_exception)

        # Assert
        self.assertEqual(mock_exc_info.call_count, 4)
        mock_getinnerframes.assert_called_once_with("traceback_object")

        # Check that format_log_message was called with the correct parameters
        mock_format_log_message.assert_called_once_with(
            message="Error while executing periodic background task",
            data={"function": "test_function"},
            exception=test_exception,
            username=None,
        )

        # Check that the error was logged
        mock_logger.error.assert_has_calls([call("Formatted log message")])

        # Check that send_task_exception_notification was called with the correct parameters
        mock_send_notification.assert_called_once_with(
            function="test_function", arguments=None, user=None, exception=test_exception, product=None
        )

    @patch("application.background_tasks.services.task_base.send_task_exception_notification")
    @patch("application.background_tasks.services.task_base.format_log_message")
    @patch("application.background_tasks.services.task_base.logger")
    @patch("application.background_tasks.services.task_base.sys.exc_info")
    def test_handle_periodic_task_exception_without_frames(
        self, mock_exc_info, mock_logger, mock_format_log_message, mock_send_notification
    ):
        # Setup
        test_exception = Exception("Test exception")
        mock_exc_info.return_value = (None, None, None)
        mock_format_log_message.return_value = "Formatted log message"

        # Execute
        _handle_periodic_task_exception(test_exception)

        # Assert
        self.assertEqual(mock_exc_info.call_count, 3)

        # Check that format_log_message was called with the correct parameters
        mock_format_log_message.assert_called_once_with(
            message="Error while executing periodic background task",
            data={},
            exception=test_exception,
            username=None,
        )

        # Check that the error was logged
        mock_logger.error.assert_has_calls([call("Formatted log message")])

        # Check that send_task_exception_notification was called with the correct parameters
        mock_send_notification.assert_called_once_with(
            function=None, arguments=None, user=None, exception=test_exception, product=None
        )

    @patch("application.background_tasks.services.task_base.send_task_exception_notification")
    @patch("application.background_tasks.services.task_base.format_log_message")
    @patch("application.background_tasks.services.task_base.logger")
    @patch("application.background_tasks.services.task_base.sys.exc_info")
    @patch("application.background_tasks.services.task_base.inspect.getinnerframes")
    def test_handle_periodic_task_exception_with_insufficient_frames(
        self, mock_getinnerframes, mock_exc_info, mock_logger, mock_format_log_message, mock_send_notification
    ):
        # Setup
        test_exception = Exception("Test exception")
        mock_exc_info.return_value = (None, None, "traceback_object")

        # Create a mock frame with only one frame (less than required)
        mock_getinnerframes.return_value = [MagicMock()]

        mock_format_log_message.return_value = "Formatted log message"

        # Execute
        _handle_periodic_task_exception(test_exception)

        # Assert
        self.assertEqual(mock_exc_info.call_count, 4)
        mock_getinnerframes.assert_called_once_with("traceback_object")

        # Check that format_log_message was called with the correct parameters
        mock_format_log_message.assert_called_once_with(
            message="Error while executing periodic background task",
            data={},
            exception=test_exception,
            username=None,
        )

        # Check that the error was logged
        mock_logger.error.assert_has_calls([call("Formatted log message")])

        # Check that send_task_exception_notification was called with the correct parameters
        mock_send_notification.assert_called_once_with(
            function=None, arguments=None, user=None, exception=test_exception, product=None
        )

    # ---------------------------------------------------------------
    # _delete_older_entries
    # ---------------------------------------------------------------

    @patch("application.background_tasks.services.task_base.Settings.load")
    def test_delete_older_entries(self, mock_settings_load):
        # Setup settings
        mock_settings = MagicMock()
        mock_settings.periodic_task_max_entries = 8
        mock_settings_load.return_value = mock_settings
        # Setup - Create 15 periodic tasks with the same task name
        from django.utils import timezone

        from application.background_tasks.models import Periodic_Task
        from application.background_tasks.types import Status

        task_name = "test_task"
        other_task_name = "other_task"

        # Create 15 tasks with different start times for the main task
        for i in range(15):
            Periodic_Task.objects.create(
                task=task_name,
                start_time=timezone.now() - timezone.timedelta(minutes=i),
                status=Status.STATUS_SUCCESS,
                message=f"Task {i}",
            )

        # Create 5 tasks with a different task name (should not be affected)
        for i in range(5):
            Periodic_Task.objects.create(
                task=other_task_name,
                start_time=timezone.now() - timezone.timedelta(minutes=i),
                status=Status.STATUS_SUCCESS,
                message=f"Other task {i}",
            )

        # Execute
        _delete_older_entries(task_name)

        # Assert
        mock_settings_load.assert_called_once()

        # Should keep only the 8 most recent tasks for task_name
        remaining_tasks = Periodic_Task.objects.filter(task=task_name).count()
        self.assertEqual(remaining_tasks, 8, "Should keep exactly 8 most recent tasks")

        # Check that the oldest tasks were deleted
        oldest_remaining = Periodic_Task.objects.filter(task=task_name).order_by("start_time").first()
        self.assertEqual(oldest_remaining.message, "Task 7", "The oldest remaining task should be Task 9")

        # Check that the newest tasks were kept
        newest_remaining = Periodic_Task.objects.filter(task=task_name).order_by("-start_time").first()
        self.assertEqual(newest_remaining.message, "Task 0", "The newest task should be Task 0")

        # Check that other task entries were not affected
        other_tasks_count = Periodic_Task.objects.filter(task=other_task_name).count()
        self.assertEqual(other_tasks_count, 5, "Tasks with different names should not be affected")
