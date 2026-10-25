import logging
import re
import traceback
from typing import Any, Optional

import inflect
from django.db.models.deletion import ProtectedError, RestrictedError
from django.http import HttpRequest, HttpResponse
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.views import exception_handler, set_rollback

from application.access_control.services.current_user import get_current_username
from application.commons.services.global_request import get_current_request
from application.commons.services.log_message import format_log_message
from application.notifications.services.send_notifications_exception import (
    send_exception_notification,
)

logger = logging.getLogger("secobserve.exception_handler")

EXCEPTION_TO_NOTIFY = "secobserve_exception_to_notify"


def custom_exception_handler(exc: Exception, context: dict) -> Response:
    response: Optional[Response]
    if isinstance(exc, (ProtectedError, RestrictedError)):
        # An object cannot be deleted because it has dependent objects.
        response = Response()
        response.status_code = HTTP_409_CONFLICT
        response.data = {}
        response.data["message"] = format_exception_message(exc)
    else:
        # Call REST framework's default exception handler first,
        # to get the standard error response.
        response = exception_handler(exc, context)

        if response is None:
            # There is no standard error response, so we assume an unexpected
            # exception. It is logged but no details are given to the user,
            # to avoid leaking internal technical information.
            response = Response()
            response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
            response.data = {}
            response.data["message"] = "Internal server error, check logs for details"
            logger.error(format_log_message(response=response, exception=exc, username=get_current_username()))
            logger.error(traceback.format_exc())
            _handle_server_error(exc)
        else:
            if response.status_code < 500:
                if response.status_code in (HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN):
                    logger.warning(
                        format_log_message(response=response, exception=exc, username=get_current_username())
                    )

                # HTTP status codes lower than 500 are no technical errors.
                # They need not to be logged and we provide the exception
                # message in the response.
                response.data = {}
                response.data["message"] = format_exception_message(exc)
            else:
                # HTTP status code 500 or higher are technical errors.
                # They get logged but no details are given to the user,
                # to avoid leaking internal technical information.
                logger.error(format_log_message(response=response, exception=exc, username=get_current_username()))
                logger.error(traceback.format_exc())
                _handle_server_error(exc)
                response.data = {}
                response.data["message"] = "Internal server error, check logs for details"

    return response


def _handle_server_error(exc: Exception) -> None:
    # REST framework only rolls back the request transaction for an APIException.
    set_rollback()

    request = get_current_request()
    if request:
        # The notification is written to the database, which has to wait until the rollback is done.
        setattr(request, EXCEPTION_TO_NOTIFY, exc)
    else:
        send_exception_notification(exc)


class ExceptionNotificationMiddleware:
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Middleware runs outside of the transaction of ATOMIC_REQUESTS.
        response = self.get_response(request)

        exception = getattr(request, EXCEPTION_TO_NOTIFY, None)
        if exception:
            send_exception_notification(exception)

        return response


def format_exception_message(exc: Exception) -> str:
    if hasattr(exc, "detail") and exc.detail and isinstance(exc.detail, dict):
        message_list = []
        for key in exc.detail:
            message_list.extend(_format_validation_messages(_format_field_name(key), exc.detail.get(key)))
        return "\n".join(message_list)

    if hasattr(exc, "detail") and exc.detail and isinstance(exc.detail, list) and len(exc.detail) > 0:
        return " / ".join(exc.detail)

    if (
        hasattr(exc, "args")
        and exc.args
        and isinstance(exc.args[0], str)
        and ("protected foreign keys" in exc.args[0] or "restricted foreign keys" in exc.args[0])
    ):
        return _format_referenced_foreign_keys(exc.args[0])

    return str(exc)


def _format_field_name(field_name: str) -> str:
    return field_name.replace("_", " ").capitalize()


def _format_validation_messages(label: str, detail: Any) -> list[str]:
    if isinstance(detail, dict):
        messages = []
        for key, value in detail.items():
            if isinstance(key, int):
                # Errors of list items are reported per index
                messages.extend(_format_validation_messages(f"{label} (entry {key + 1})", value))
            else:
                messages.extend(_format_validation_messages(f"{label} / {_format_field_name(key)}", value))
        return messages

    if isinstance(detail, list):
        return [message for item in detail for message in _format_validation_messages(label, item)]

    return [f"{label}: {detail}"]


def _format_referenced_foreign_keys(message: str) -> str:
    results = re.findall(r"'[a-zA-Z\.\_]*'", message)
    if len(results) >= 2:
        first_result = ""
        second_results = []
        p = inflect.engine()
        for i, result in enumerate(results):
            if i == 0:
                first_result = result.replace("'", "")
            else:
                second_results.append(p.plural(result.split(".")[0].replace("'", "")))
        second_result = ", ".join(second_results)

        return f"Cannot delete {first_result} because it still has {second_result}."

    return message
