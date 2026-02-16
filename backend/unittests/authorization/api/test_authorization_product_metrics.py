from datetime import timedelta

from django.utils import timezone

from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationProductMetrics(TestAuthorizationBase):
    def test_authorization_metrics(self):
        yesterday = (timezone.now() - timedelta(days=1)).date().isoformat()
        today = timezone.now().date().isoformat()

        expected_data = "{'active_critical': 7, 'active_high': 9, 'active_medium': 11, 'active_low': 13, 'active_none': 15, 'active_unknown': 17, 'open': 19, 'affected': 21, 'resolved': 23, 'duplicate': 25, 'false_positive': 27, 'in_review': 29, 'not_affected': 31, 'not_security': 33, 'risk_accepted': 35}"
        self._test_api(
            APITest(
                "db_admin",
                "get",
                "/api/metrics/product_metrics_current/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'2023-07-09': {'active_critical': 5, 'active_high': 7, 'active_medium': 9, 'active_low': 11, 'active_none': 13, 'active_unknown': 15, 'open': 17, 'affected': 19, 'resolved': 21, 'duplicate': 23, 'false_positive': 25, 'in_review': 27, 'not_affected': 29, 'not_security': 31, 'risk_accepted': 33}, '2023-07-10': {'active_critical': 7, 'active_high': 9, 'active_medium': 11, 'active_low': 13, 'active_none': 15, 'active_unknown': 17, 'open': 19, 'affected': 21, 'resolved': 23, 'duplicate': 25, 'false_positive': 27, 'in_review': 29, 'not_affected': 31, 'not_security': 33, 'risk_accepted': 35}}"
        expected_data = expected_data.replace("2023-07-10", today)
        expected_data = expected_data.replace("2023-07-09", yesterday)
        self._test_api(
            APITest(
                "db_admin",
                "get",
                "/api/metrics/product_metrics_timeline/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'active_critical': 2, 'active_high': 3, 'active_medium': 4, 'active_low': 5, 'active_none': 6, 'active_unknown': 7, 'open': 8, 'affected': 9, 'resolved': 10, 'duplicate': 11, 'false_positive': 12, 'in_review': 13, 'not_affected': 14, 'not_security': 15, 'risk_accepted': 16}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/metrics/product_metrics_current/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'2023-07-09': {'active_critical': 1, 'active_high': 2, 'active_medium': 3, 'active_low': 4, 'active_none': 5, 'active_unknown': 6, 'open': 7, 'affected': 8, 'resolved': 9, 'duplicate': 10, 'false_positive': 11, 'in_review': 12, 'not_affected': 13, 'not_security': 14, 'risk_accepted': 15}, '2023-07-10': {'active_critical': 2, 'active_high': 3, 'active_medium': 4, 'active_low': 5, 'active_none': 6, 'active_unknown': 7, 'open': 8, 'affected': 9, 'resolved': 10, 'duplicate': 11, 'false_positive': 12, 'in_review': 13, 'not_affected': 14, 'not_security': 15, 'risk_accepted': 16}}"
        expected_data = expected_data.replace("2023-07-10", today)
        expected_data = expected_data.replace("2023-07-09", yesterday)
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/metrics/product_metrics_timeline/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'active_critical': 2, 'active_high': 3, 'active_medium': 4, 'active_low': 5, 'active_none': 6, 'active_unknown': 7, 'open': 8, 'affected': 9, 'resolved': 10, 'duplicate': 11, 'false_positive': 12, 'in_review': 13, 'not_affected': 14, 'not_security': 15, 'risk_accepted': 16}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/metrics/product_metrics_current/?product_id=1",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'2023-07-09': {'active_critical': 1, 'active_high': 2, 'active_medium': 3, 'active_low': 4, 'active_none': 5, 'active_unknown': 6, 'open': 7, 'affected': 8, 'resolved': 9, 'duplicate': 10, 'false_positive': 11, 'in_review': 12, 'not_affected': 13, 'not_security': 14, 'risk_accepted': 15}, '2023-07-10': {'active_critical': 2, 'active_high': 3, 'active_medium': 4, 'active_low': 5, 'active_none': 6, 'active_unknown': 7, 'open': 8, 'affected': 9, 'resolved': 10, 'duplicate': 11, 'false_positive': 12, 'in_review': 13, 'not_affected': 14, 'not_security': 15, 'risk_accepted': 16}}"
        expected_data = expected_data.replace("2023-07-10", today)
        expected_data = expected_data.replace("2023-07-09", yesterday)
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/metrics/product_metrics_timeline/?product_id=1",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/metrics/product_metrics_current/?product_id=2",
                None,
                403,
                expected_data,
            )
        )
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/metrics/product_metrics_timeline/?product_id=2",
                None,
                403,
                expected_data,
            )
        )
