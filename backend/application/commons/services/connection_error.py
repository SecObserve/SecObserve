import logging

import requests

from application.commons.services.log_message import format_log_message

logger = logging.getLogger("secobserve.commons")


def get_connection_error_message(message: str, exception: Exception) -> str:
    """
    Returns an error message for a failed request to a user defined URL, that can be shown to users.
    The exception text is only logged, it would tell users about the network of the backend otherwise,
    e.g. by the different texts for a closed port and an open port without an HTTP service.
    """

    logger.warning(format_log_message(message=message, exception=exception))

    # JIRAError has the status code itself, requests.HTTPError has it in its response
    status_code = getattr(exception, "status_code", None) or getattr(
        getattr(exception, "response", None), "status_code", None
    )
    if status_code:
        return f"{message}: HTTP status {status_code}"

    return f"{message}, see backend log for details"


def raise_for_status(response: requests.Response) -> None:
    # Redirects are not followed for user defined URLs, so they are errors as well
    if 300 <= response.status_code < 400:
        raise requests.exceptions.HTTPError(
            f"{response.status_code} Redirect for url: {response.url}", response=response
        )
    response.raise_for_status()
