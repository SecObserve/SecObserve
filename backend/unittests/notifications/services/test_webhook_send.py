import base64
import io
from ipaddress import ip_network
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from requests import ConnectionError as RequestsConnectionError
from requests import Response
from requests.exceptions import ChunkedEncodingError

from application.notifications.services.send_notifications_base import (
    _validate_webhook_url,
)
from application.notifications.services.webhook_send import (
    generate_webhook_secret,
    send_webhook_request,
    sign_webhook_payload,
)


class TestSignWebhookPayload(SimpleTestCase):
    def test_standard_webhooks_vector(self):
        self.assertEqual(
            sign_webhook_payload(
                "whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw",
                "msg_p5jXN8AQM9LWM0D4loKWxJek",
                1614265330,
                '{"test": 2432232314}',
            ),
            "v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=",
        )

    def test_generate_webhook_secret(self):
        secret = generate_webhook_secret()
        self.assertTrue(secret.startswith("whsec_"))
        self.assertEqual(len(base64.b64decode(secret[len("whsec_") :])), 32)
        self.assertNotEqual(secret, generate_webhook_secret())


def _response(status_code: int, text: str = "") -> Response:
    response = Response()
    response.status_code = status_code
    response.raw = io.BytesIO(text.encode())
    return response


@override_settings(WEBHOOK_TIMEOUT=7, WEBHOOK_ALLOWED_NETWORKS=[])
class TestSendWebhookRequest(SimpleTestCase):
    secret = generate_webhook_secret()

    def setUp(self):
        self.mock_time = self._patch("time.time", 1700000000)
        self.mock_validate = self._patch("_validate_webhook_url", True)
        self.mock_post = self._patch("requests.post")

    def _patch(self, name, return_value=None):
        patcher = patch(f"application.notifications.services.webhook_send.{name}", return_value=return_value)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _send(self):
        return send_webhook_request("https://example.com/hook", self.secret, "msg_1", '{"a": 1}')

    def test_headers_and_options(self):
        self.mock_post.return_value = _response(204)
        result = self._send()

        _, kwargs = self.mock_post.call_args
        self.assertEqual(self.mock_post.call_args.args[0], "https://example.com/hook")
        self.assertEqual(kwargs["data"], '{"a": 1}')
        headers = kwargs["headers"]
        self.assertEqual(headers["webhook-id"], "msg_1")
        self.assertEqual(headers["webhook-timestamp"], "1700000000")
        self.assertEqual(
            headers["webhook-signature"], sign_webhook_payload(self.secret, "msg_1", 1700000000, '{"a": 1}')
        )
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["User-Agent"], "SecObserve-Webhooks")
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["timeout"], (7, 7))
        self.assertTrue(kwargs["stream"])
        self.assertTrue(result.succeeded)
        self.assertFalse(result.retryable)

    def test_503_is_retryable(self):
        self.mock_post.return_value = _response(503, "x" * 5000)
        result = self._send()
        self.assertFalse(result.succeeded)
        self.assertTrue(result.retryable)
        self.assertEqual(result.status_code, 503)
        self.assertTrue(result.error.startswith("HTTP 503"))
        self.assertLessEqual(len(result.error), 1024)

    def test_error_body_read_is_bounded(self):
        response = _response(503)
        chunks = iter([b"x" * 600] * 100)
        response.iter_content = lambda chunk_size: chunks
        self.mock_post.return_value = response

        result = self._send()

        self.assertEqual(result.error, "HTTP 503: " + "x" * (1024 - len("HTTP 503: ")))
        # Two chunks reach the limit, the rest of the body is never read
        self.assertEqual(98, len(list(chunks)))

    def test_error_body_read_failure_keeps_the_status_code(self):
        response = _response(503)
        response.iter_content = lambda chunk_size: (_ for _ in ()).throw(ChunkedEncodingError("broken"))
        self.mock_post.return_value = response

        result = self._send()

        self.assertEqual(result.status_code, 503)
        self.assertTrue(result.retryable)
        self.assertEqual(result.error, "HTTP 503: ChunkedEncodingError while reading the body")

    def test_error_body_ignores_the_receivers_charset(self):
        response = _response(503)
        response.raw = io.BytesIO(b"bad \xff byte")
        response.encoding = "bogus"
        self.mock_post.return_value = response

        result = self._send()

        self.assertEqual(result.status_code, 503)
        self.assertTrue(result.retryable)
        self.assertEqual(result.error, "HTTP 503: bad \ufffd byte")

    def test_response_is_closed(self):
        for status_code in (204, 503):
            with self.subTest(status_code=status_code):
                response = _response(status_code, "body")
                self.mock_post.return_value = response

                with patch.object(response, "close", wraps=response.close) as mock_close:
                    self._send()

                mock_close.assert_called_once()

    def test_429_is_retryable(self):
        self.mock_post.return_value = _response(429)
        result = self._send()
        self.assertTrue(result.retryable)
        self.assertTrue(result.error.startswith("HTTP 429"))

    def test_400_is_permanent(self):
        self.mock_post.return_value = _response(400)
        result = self._send()
        self.assertFalse(result.succeeded)
        self.assertFalse(result.retryable)
        self.assertTrue(result.error.startswith("HTTP 400"))

    def test_302_is_permanent(self):
        self.mock_post.return_value = _response(302)
        result = self._send()
        self.assertFalse(result.succeeded)
        self.assertFalse(result.retryable)
        self.assertTrue(result.error.startswith("HTTP 302"))

    def test_connection_error_is_retryable(self):
        self.mock_post.side_effect = RequestsConnectionError("boom")
        result = self._send()
        self.assertIsNone(result.status_code)
        self.assertTrue(result.retryable)
        self.assertIn("ConnectionError", result.error)

    def test_rejected_url_is_not_sent(self):
        self.mock_validate.return_value = False
        result = self._send()
        self.mock_post.assert_not_called()
        self.assertTrue(result.retryable)
        self.assertEqual(result.error, "URL rejected, see the backend log")


def _addrinfo(*ips):
    return [(2, 1, 6, "", (ip, 0)) for ip in ips]


class TestValidateWebhookUrlAllowedNetworks(SimpleTestCase):
    allowed = [ip_network("10.0.0.0/8")]

    def setUp(self):
        patcher = patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
        self.mock_dns = patcher.start()
        self.addCleanup(patcher.stop)

    def test_https_private_allowlisted(self):
        self.mock_dns.return_value = _addrinfo("10.1.2.3")
        self.assertTrue(_validate_webhook_url("https://h.example/x", self.allowed))

    def test_https_private_without_allowlist(self):
        self.mock_dns.return_value = _addrinfo("10.1.2.3")
        self.assertFalse(_validate_webhook_url("https://h.example/x"))

    def test_http_private_allowlisted(self):
        self.mock_dns.return_value = _addrinfo("10.1.2.3")
        self.assertTrue(_validate_webhook_url("http://h.example/x", self.allowed))

    def test_http_public(self):
        self.mock_dns.return_value = _addrinfo("93.184.216.34")
        self.assertFalse(_validate_webhook_url("http://h.example/x", self.allowed))

    def test_http_mixed(self):
        self.mock_dns.return_value = _addrinfo("10.1.2.3", "93.184.216.34")
        self.assertFalse(_validate_webhook_url("http://h.example/x", self.allowed))

    def test_ftp(self):
        self.mock_dns.return_value = _addrinfo("10.1.2.3")
        self.assertFalse(_validate_webhook_url("ftp://h.example/x", self.allowed))


class TestValidateWebhookUrlMalformed(SimpleTestCase):
    def test_invalid_port(self):
        self.assertFalse(_validate_webhook_url("https://host:abc/"))

    def test_invalid_idna_label(self):
        self.assertFalse(_validate_webhook_url(f"https://{'a' * 64}.example/"))

    @override_settings(WEBHOOK_ALLOWED_NETWORKS=[])
    @patch("application.notifications.services.webhook_send.requests.post")
    def test_send_malformed_url_is_not_sent(self, mock_post):
        result = send_webhook_request("https://host:abc/", generate_webhook_secret(), "msg_1", "{}")
        mock_post.assert_not_called()
        self.assertTrue(result.retryable)
        self.assertEqual(result.error, "URL rejected, see the backend log")
