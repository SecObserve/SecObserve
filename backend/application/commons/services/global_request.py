from threading import current_thread
from typing import Any, Optional

from rest_framework.request import Request
from rest_framework.response import Response

_requests: dict[str, Request] = {}


def get_current_request() -> Optional[Request]:
    return _requests.get(current_thread().name)


class GlobalRequestMiddleware:
    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request: Request) -> Response:
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        _requests[current_thread().name] = request

        try:
            return self.get_response(request)
        finally:
            # Code to be executed for each request/response after the view is called.
            # The request must not outlive the response, otherwise the thread would keep it
            # and everything attached to it, and the next code running in this thread outside
            # of a request would see the user of the previous one.
            _requests.pop(current_thread().name, None)
