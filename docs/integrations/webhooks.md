# Outbound webhooks

SecObserve can send events to any HTTP endpoint, for example to feed a SIEM, a chat bridge or a workflow engine. Requests follow the [Standard Webhooks](https://www.standardwebhooks.com/) v1 conventions, so existing verification libraries work. The chat channels with their own message formats are described in [Notification channels](notifications.md).

## Scopes and permissions

A webhook belongs to one of three scopes:

| Scope | Receives events of |
|---|---|
| Global | All products. Only superusers can manage global webhooks. |
| Product group | All products of the group. |
| Product | The product. |

Events that belong to no product (for example general rules) are only sent to global webhooks.

The permissions `Webhook View`, `Webhook Edit`, `Webhook Delete` and `Webhook Create` are granted like the permissions for API configurations: `Webhook View` to the roles Reader and Writer, all four to Maintainer and Owner.

A webhook can be restricted to a subset of the event types below, and, for observation and assessment events, to a minimum severity (`Unknown`, `None`, `Low`, `Medium`, `High`, `Critical`).

## Events

Every request body is a JSON object with the event `type`, the `timestamp` of the event (ISO 8601) and the event `data`. Fields are only ever added, never renamed or removed. The same event is sent byte-identical to every matching webhook and on every retry.

> **Untrusted data**
>
> Titles, component names, comments and remarks in the payload come from scanners and users. Treat them as data: escape them before rendering, never execute or interpolate them into commands or queries.

| Type | Sent when |
|---|---|
| `observation.created` | An observation is created by an import or manually and its status is active after rules and VEX statements are applied. |
| `observation.review_requested` | An observation gets the status "In review", the same condition as the [review notification](../usage/notifications.md). |
| `assessment.approval_requested` | An assessment is saved and needs approval. |
| `assessment.approval_decided` | An assessment is approved or rejected. |
| `rule.approval_requested` | A rule is created or changed and needs approval. |
| `rule.approval_decided` | A rule is approved or rejected. |
| `import.completed` | Every import finished: file upload, API import, OSV scan and VulnerableCode scan. |
| `security_gate.changed` | The security gate of a product switched between passed and failed. |

The type `webhook.test` is only sent by the test function of a webhook and cannot be subscribed to.

The `product` object is part of every event. `product_group` is `null` when the product is not in a group, `security_gate_passed` is `null` when the gate is not evaluated. The `url` fields point into the SecObserve frontend.

### observation.created and observation.review_requested

```json
{
  "type": "observation.created",
  "timestamp": "2026-11-02T08:15:30.123456+00:00",
  "data": {
    "product": {
      "id": 7,
      "name": "Payments",
      "product_group": {"id": 2, "name": "Backend"},
      "security_gate_passed": true,
      "url": "https://secobserve.example.com/#/products/7/show"
    },
    "observation": {
      "id": 1234,
      "title": "Prototype pollution in lodash",
      "severity": "High",
      "status": "Open",
      "priority": null,
      "vulnerability_id": "CVE-2021-23337",
      "component": "lodash:4.17.15",
      "branch": "main",
      "service": null,
      "scanner": "Trivy",
      "url": "https://secobserve.example.com/#/observations/1234/show"
    }
  }
}
```

`priority` is a number or `null`, `branch` and `service` are `null` when not set.

### assessment.approval_requested and assessment.approval_decided

```json
{
  "type": "assessment.approval_decided",
  "timestamp": "2026-11-02T09:02:11.504321+00:00",
  "data": {
    "product": {
      "id": 7,
      "name": "Payments",
      "product_group": null,
      "security_gate_passed": true,
      "url": "https://secobserve.example.com/#/products/7/show"
    },
    "observation": {
      "id": 1234,
      "title": "Prototype pollution in lodash",
      "severity": "High",
      "status": "Not affected",
      "priority": null,
      "vulnerability_id": "CVE-2021-23337",
      "component": "lodash:4.17.15",
      "branch": "main",
      "service": null,
      "scanner": "Trivy",
      "url": "https://secobserve.example.com/#/observations/1234/show"
    },
    "assessment": {
      "id": 981,
      "user": "alice",
      "severity": "",
      "status": "Not affected",
      "priority": null,
      "comment": "The vulnerable function is not called",
      "assessment_status": "Approved",
      "approval_user": "bob",
      "rejection_remark": "",
      "url": "https://secobserve.example.com/#/observation_logs/981/show"
    }
  }
}
```

`assessment_status` is `Needs approval` for the request and `Approved`, `Approved with edits` or `Rejected` for the decision. `approval_user` is `null` until a decision is made.

### rule.approval_requested and rule.approval_decided

```json
{
  "type": "rule.approval_requested",
  "timestamp": "2026-11-02T10:20:00.000000+00:00",
  "data": {
    "product": {
      "id": 7,
      "name": "Payments",
      "product_group": null,
      "security_gate_passed": true,
      "url": "https://secobserve.example.com/#/products/7/show"
    },
    "rule": {
      "id": 15,
      "name": "Ignore test fixtures",
      "scope": "product",
      "user": "alice",
      "approval_status": "Needs approval",
      "approval_user": null,
      "rejection_remark": "",
      "url": "https://secobserve.example.com/#/product_rules/15/show"
    }
  }
}
```

`scope` is `product` or `general`. For a general rule `product` is `null` and only global webhooks receive the event.

### import.completed

```json
{
  "type": "import.completed",
  "timestamp": "2026-11-02T08:15:31.000000+00:00",
  "data": {
    "product": {
      "id": 7,
      "name": "Payments",
      "product_group": {"id": 2, "name": "Backend"},
      "security_gate_passed": true,
      "url": "https://secobserve.example.com/#/products/7/show"
    },
    "import": {
      "parser": "Trivy Filesystem",
      "branch": "main",
      "service": null,
      "filename": "trivy.json",
      "api_configuration": "",
      "observations_new": 12,
      "observations_updated": 40,
      "observations_resolved": 3
    }
  }
}
```

`filename` is empty for API imports and scans, `api_configuration` is empty for file uploads. The numbers are the same as in the result of the import in the REST API.

### security_gate.changed

```json
{
  "type": "security_gate.changed",
  "timestamp": "2026-11-02T08:15:31.250000+00:00",
  "data": {
    "product": {
      "id": 7,
      "name": "Payments",
      "product_group": {"id": 2, "name": "Backend"},
      "security_gate_passed": false,
      "url": "https://secobserve.example.com/#/products/7/show"
    }
  }
}
```

The new state is `product.security_gate_passed`.

## Requests and signature

Each delivery is an HTTP `POST` with these headers:

| Header | Value |
|---|---|
| `Content-Type` | `application/json` |
| `User-Agent` | `SecObserve-Webhooks` |
| `webhook-id` | UUID of the event. It is the same for all webhooks that get the event and for every retry of a delivery. |
| `webhook-timestamp` | Unix time in seconds of the attempt. |
| `webhook-signature` | `v1,` followed by the base64 encoded HMAC-SHA256 of `{webhook-id}.{webhook-timestamp}.{body}`. |

The signing key is the secret of the webhook: `whsec_` followed by base64 of 32 random bytes. Base64-decode the part after `whsec_` to get the key. The secret is generated by SecObserve and shown only when the webhook is created or its secret is rotated. It is stored encrypted.

Every 2xx response is a success. Redirects are not followed.

### Reference receiver

A receiver with the Python standard library only. It verifies the signature, rejects timestamps older than five minutes and answers `204`.

```python
import base64, hashlib, hmac, json, os, time
from http.server import BaseHTTPRequestHandler, HTTPServer

KEY = base64.b64decode(os.environ["WEBHOOK_SECRET"].removeprefix("whsec_"))

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        msg_id, ts = self.headers["webhook-id"], self.headers["webhook-timestamp"]
        expected = base64.b64encode(hmac.new(KEY, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
        received = [s.split(",", 1)[1] for s in self.headers["webhook-signature"].split()]
        ok = abs(time.time() - int(ts)) < 300 and any(hmac.compare_digest(expected, s) for s in received)
        self.send_response(204 if ok else 401)
        self.end_headers()
        if ok:
            print(json.loads(body)["type"], msg_id, flush=True)

HTTPServer(("", 8080), Handler).serve_forever()
```

### Receiver best practices

* Verify the signature over the raw body before parsing it, and compare in constant time.
* Check `webhook-timestamp` to reject replays.
* Deduplicate on `webhook-id`, delivery is at least once.
* Do not rely on the order of events.
* Answer quickly with a 2xx and process asynchronously. The request times out after `WEBHOOK_TIMEOUT` seconds.
* Treat all strings in the payload as untrusted.

## Delivery

* Events are written to an outbox in the transaction that causes them, so no event is lost or sent for a rolled back change. The webhook is normally called about 2 seconds after the commit, at worst about 60 seconds later, when the per-minute sweeper picks it up.
* Delivery is at least once. A receiver can see the same `webhook-id` more than once.
* There is no ordering guarantee between events. The deliveries of one webhook are sent oldest first.
* A failed attempt is retried after the delays in `WEBHOOK_RETRY_DELAYS`. The delay applies to the whole endpoint: no other delivery of this webhook is sent until it has passed.
* A delivery is marked `Failed` after `len(WEBHOOK_RETRY_DELAYS) + 1` attempts when the errors are retryable (no response, `408`, `429` or `5xx`), and immediately on any other response. Other deliveries of the webhook continue until `WEBHOOK_FAILURE_ALERT_THRESHOLD` consecutive failures, then the endpoint backs off too.
* When the consecutive failures of a webhook reach `WEBHOOK_FAILURE_ALERT_THRESHOLD`, one alert is sent to the exception notification channels.
* Of an error response only the first 1024 bytes are kept in the delivery log. The log is kept for `WEBHOOK_DELIVERY_RETENTION_DAYS` days.
* Delivery needs the [background (huey) consumer](../getting_started/installation.md) to run. Without it, deliveries stay pending.

## Configuration

The behavior is set with the five `WEBHOOK_*` [environment variables](../getting_started/configuration.md#backend). Invalid values stop the backend at startup.

### URL policy

The URL of a webhook must use `https`. A host that resolves only into the networks of `WEBHOOK_ALLOWED_NETWORKS` is the exception: it may be a private address and may use `http`.

> **Keep the allowed networks narrow**
>
> Every user who can manage the webhooks of a product (Maintainer, Owner) can point a webhook at any address inside the allowed networks and send signed requests there. List only the networks that need it, and as small as possible.

### Internal certificate authority

When the receiver uses a certificate of an internal CA, add the CA to the bundle that the backend uses and set `REQUESTS_CA_BUNDLE` to the path of that bundle.
