import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings

from application.notifications.services.send_notifications_base import (
    _validate_webhook_url,
)

SECRET_PREFIX = "whsec_"
MAX_ERROR_LENGTH = 1024


@dataclass(frozen=True)
class Webhook_Send_Result:
    status_code: Optional[int]
    error: str

    @property
    def succeeded(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 300

    @property
    def retryable(self) -> bool:
        if self.succeeded:
            return False
        return self.status_code is None or self.status_code in (408, 429) or self.status_code >= 500


def generate_webhook_secret() -> str:
    return SECRET_PREFIX + base64.b64encode(secrets.token_bytes(32)).decode()


def sign_webhook_payload(secret: str, message_id: str, timestamp: int, body: str) -> str:
    key = base64.b64decode(secret.removeprefix(SECRET_PREFIX))
    signed_content = f"{message_id}.{timestamp}.{body}".encode()
    return "v1," + base64.b64encode(hmac.new(key, signed_content, hashlib.sha256).digest()).decode()


def send_webhook_request(url: str, secret: str, message_id: str, body: str) -> Webhook_Send_Result:
    if not _validate_webhook_url(url, settings.WEBHOOK_ALLOWED_NETWORKS):
        return Webhook_Send_Result(None, "URL rejected, see the backend log")

    timestamp = int(time.time())
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SecObserve-Webhooks",
        "webhook-id": message_id,
        "webhook-timestamp": str(timestamp),
        "webhook-signature": sign_webhook_payload(secret, message_id, timestamp, body),
    }
    try:
        response = requests.post(
            url,
            data=body,
            headers=headers,
            allow_redirects=False,
            timeout=(settings.WEBHOOK_TIMEOUT, settings.WEBHOOK_TIMEOUT),
            stream=True,
        )
    except requests.RequestException as e:
        return Webhook_Send_Result(None, f"{type(e).__name__}: {e}"[:MAX_ERROR_LENGTH])

    with response:
        if 200 <= response.status_code < 300:
            return Webhook_Send_Result(response.status_code, "")
        return Webhook_Send_Result(
            response.status_code, f"HTTP {response.status_code}: {_read_body_start(response)}"[:MAX_ERROR_LENGTH]
        )


def _read_body_start(response: requests.Response) -> str:
    # The body is untrusted: read only what the error field keeps, never the whole (decompressed) body
    content = b""
    try:
        for chunk in response.iter_content(chunk_size=MAX_ERROR_LENGTH):
            content += chunk
            if len(content) >= MAX_ERROR_LENGTH:
                break
    except requests.RequestException as e:
        return f"{type(e).__name__} while reading the body"
    return content[:MAX_ERROR_LENGTH].decode(response.encoding or "utf-8", errors="replace")
