from datetime import datetime, timezone

from application.audit_trail.models import Product_Audit_Event
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)

URL = "/api/product_audit_events/"

EVENT_1 = "{'id': 1, 'product_name': 'db_product_internal', 'is_product_group': False, 'created': '2026-01-01T01:00:00+01:00', 'user_full_name': '', 'object_type': 'Product', 'object_id': 1, 'object_name': 'db_product_internal', 'action': 'Created', 'changes': None, 'product': 1, 'user': None}"
EVENT_2 = "{'id': 2, 'product_name': 'db_product_external', 'is_product_group': False, 'created': '2026-01-02T01:00:00+01:00', 'user_full_name': '', 'object_type': 'Product', 'object_id': 2, 'object_name': 'db_product_external', 'action': 'Created', 'changes': None, 'product': 2, 'user': None}"
EVENT_3 = "{'id': 3, 'product_name': 'db_product_group', 'is_product_group': True, 'created': '2026-01-03T01:00:00+01:00', 'user_full_name': '', 'object_type': 'Product', 'object_id': 3, 'object_name': 'db_product_group', 'action': 'Created', 'changes': None, 'product': 3, 'user': None}"
EVENT_99 = "{'id': 4, 'product_name': 'db_product_deleted', 'is_product_group': False, 'created': '2026-01-04T01:00:00+01:00', 'user_full_name': '', 'object_type': 'Product', 'object_id': 99, 'object_name': 'db_product_deleted', 'action': 'Created', 'changes': None, 'product': 99, 'user': None}"


def _list(*events: str) -> str:
    return f"{{'count': {len(events)}, 'next': None, 'previous': None, 'results': [{', '.join(events)}]}}"


class TestAuthorizationProductAuditEvents(TestAuthorizationBase):
    def test_authorization_product_audit_events_product_member(self):
        self._test_authorization_product_audit_events()

    def test_authorization_product_audit_events_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_product_audit_events()

    def _test_authorization_product_audit_events(self):
        # The preparation of the authorization groups records events for the changed members
        Product_Audit_Event.objects.all().delete()
        for event_id, (product_id, product_name, is_product_group) in enumerate(
            (
                (1, "db_product_internal", False),
                (2, "db_product_external", False),
                (3, "db_product_group", True),
                (99, "db_product_deleted", False),
            ),
            start=1,
        ):
            Product_Audit_Event.objects.create(
                id=event_id,
                product_id=product_id,
                product_name=product_name,
                is_product_group=is_product_group,
                created=datetime(2026, 1, event_id, tzinfo=timezone.utc),
                object_type="Product",
                object_id=product_id,
                object_name=product_name,
                action="Created",
            )

        expected_data = _list(EVENT_99, EVENT_3, EVENT_2, EVENT_1)
        self._test_api(APITest("db_admin", "get", URL, None, 200, expected_data))

        expected_data = _list(EVENT_99)
        self._test_api(APITest("db_admin", "get", f"{URL}?product=99", None, 200, expected_data))

        self._test_api(APITest("db_admin", "post", URL, {}, 405, None))

        expected_data = _list(EVENT_1)
        self._test_api(APITest("db_internal_write", "get", f"{URL}?product=1", None, 200, expected_data))

        self._test_api(APITest("db_internal_write", "get", URL, None, 400, None))
        self._test_api(APITest("db_internal_write", "get", f"{URL}?product=2", None, 403, None))
        self._test_api(APITest("db_internal_write", "get", f"{URL}?product=99", None, 400, None))
        self._test_api(APITest("db_internal_write", "get", f"{URL}?product=3", None, 403, None, no_second_user=True))

        expected_data = _list(EVENT_3)
        self._test_api(APITest("db_product_group_user", "get", f"{URL}?product=3", None, 200, expected_data))

        self._test_api(APITest("db_internal_read", "get", f"{URL}?product=1", None, 403, None))

        expected_data = _list(EVENT_2)
        self._test_api(APITest("db_external", "get", f"{URL}?product=2", None, 200, expected_data))
