from datetime import date, datetime, timedelta
from unittest.mock import call, patch

from django.utils import timezone

from application.core.types import Severity, Status
from application.metrics.services.metrics import (
    _initialize_response_data,
    calculate_observation_metrics_for_product,
    calculate_product_metrics,
    get_codecharta_metrics,
    get_product_metrics_current,
    get_product_metrics_timeline,
)
from unittests.base_test_case import BaseTestCase


class TestInitializeResponseData(BaseTestCase):
    def test_initialize_response_data(self):
        result = _initialize_response_data()

        expected = {
            "active_critical": 0,
            "active_high": 0,
            "active_medium": 0,
            "active_low": 0,
            "active_none": 0,
            "active_unknown": 0,
            "open": 0,
            "affected": 0,
            "resolved": 0,
            "duplicate": 0,
            "false_positive": 0,
            "in_review": 0,
            "not_affected": 0,
            "not_security": 0,
            "risk_accepted": 0,
        }
        self.assertEqual(result, expected)


class TestCalculateProductMetrics(BaseTestCase):
    @patch("application.metrics.services.metrics.Product_Metrics_Status.load")
    @patch("application.metrics.services.metrics.calculate_metrics_for_product")
    @patch("application.metrics.services.metrics.Product.objects")
    def test_calculate_product_metrics_no_products(self, mock_product_objects, mock_calc, mock_status_load):
        mock_product_objects.filter.return_value = []

        status = ProductMetricsStatusStub()
        mock_status_load.return_value = status

        result = calculate_product_metrics()

        self.assertEqual(result, "Calculated metrics for 0 products.")
        mock_product_objects.filter.assert_called_once_with(is_product_group=False)
        mock_calc.assert_not_called()
        mock_status_load.assert_called_once()

    @patch("application.metrics.services.metrics.timezone")
    @patch("application.metrics.services.metrics.Product_Metrics_Status.load")
    @patch("application.metrics.services.metrics.calculate_metrics_for_product")
    @patch("application.metrics.services.metrics.Product.objects")
    def test_calculate_product_metrics_one_product(
        self, mock_product_objects, mock_calc, mock_status_load, mock_timezone
    ):
        mock_product_objects.filter.return_value = [self.product_1]
        mock_calc.return_value = True

        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = now

        status = ProductMetricsStatusStub()
        mock_status_load.return_value = status

        result = calculate_product_metrics()

        self.assertEqual(result, "Calculated metrics for 1 product.")
        mock_calc.assert_called_once_with(self.product_1)
        self.assertEqual(status.last_calculated, now)

    @patch("application.metrics.services.metrics.timezone")
    @patch("application.metrics.services.metrics.Product_Metrics_Status.load")
    @patch("application.metrics.services.metrics.calculate_metrics_for_product")
    @patch("application.metrics.services.metrics.Product.objects")
    def test_calculate_product_metrics_multiple_products(
        self, mock_product_objects, mock_calc, mock_status_load, mock_timezone
    ):
        product_2 = type(self.product_1)
        product_2.name = "product_2"
        mock_product_objects.filter.return_value = [
            self.product_1,
            product_2,
        ]
        mock_calc.return_value = True

        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = now

        status = ProductMetricsStatusStub()
        mock_status_load.return_value = status

        result = calculate_product_metrics()

        self.assertEqual(result, "Calculated metrics for 2 products.")
        self.assertEqual(mock_calc.call_count, 2)

    @patch("application.metrics.services.metrics.timezone")
    @patch("application.metrics.services.metrics.Product_Metrics_Status.load")
    @patch("application.metrics.services.metrics.calculate_metrics_for_product")
    @patch("application.metrics.services.metrics.Product.objects")
    def test_calculate_product_metrics_some_without_changes(
        self, mock_product_objects, mock_calc, mock_status_load, mock_timezone
    ):
        product_2 = type(self.product_1)
        product_2.name = "product_2"
        mock_product_objects.filter.return_value = [
            self.product_1,
            product_2,
        ]
        mock_calc.side_effect = [True, False]

        now = datetime(2025, 6, 15, 12, 0, 0)
        mock_timezone.now.return_value = now

        status = ProductMetricsStatusStub()
        mock_status_load.return_value = status

        result = calculate_product_metrics()

        self.assertEqual(result, "Calculated metrics for 1 product.")


class TestCalculateMetricsForProduct(BaseTestCase):
    @patch("application.metrics.services.metrics.Observation.objects")
    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    @patch("application.metrics.services.metrics._get_latest_product_metrics")
    @patch("application.metrics.services.metrics.timezone")
    def test_no_previous_metrics_no_observations(
        self, mock_timezone, mock_get_latest, mock_pm_objects, mock_obs_objects
    ):
        today = date(2025, 6, 15)
        mock_timezone.localdate.return_value = today
        self.product_1.last_observation_change = datetime(2025, 6, 15, 10, 0, 0)

        mock_get_latest.return_value = None

        todays_metrics = ProductMetricsStub()
        mock_pm_objects.update_or_create.return_value = (todays_metrics, True)
        mock_obs_objects.filter.return_value.values.return_value = []

        result = calculate_observation_metrics_for_product(self.product_1)

        self.assertTrue(result)
        mock_pm_objects.update_or_create.assert_called_once()
        todays_metrics.assert_save_called(self)

    @patch("application.metrics.services.metrics.Observation.objects")
    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    @patch("application.metrics.services.metrics._get_latest_product_metrics")
    @patch("application.metrics.services.metrics.timezone")
    def test_observations_today_with_all_severities(
        self, mock_timezone, mock_get_latest, mock_pm_objects, mock_obs_objects
    ):
        today = date(2025, 6, 15)
        mock_timezone.localdate.return_value = today
        self.product_1.last_observation_change = datetime(2025, 6, 15, 10, 0, 0)

        mock_get_latest.return_value = None

        todays_metrics = ProductMetricsStub()
        mock_pm_objects.update_or_create.return_value = (todays_metrics, True)

        observations = [
            {"current_severity": Severity.SEVERITY_CRITICAL, "current_status": Status.STATUS_OPEN},
            {"current_severity": Severity.SEVERITY_HIGH, "current_status": Status.STATUS_OPEN},
            {"current_severity": Severity.SEVERITY_MEDIUM, "current_status": Status.STATUS_AFFECTED},
            {"current_severity": Severity.SEVERITY_LOW, "current_status": Status.STATUS_IN_REVIEW},
            {"current_severity": Severity.SEVERITY_NONE, "current_status": Status.STATUS_OPEN},
            {"current_severity": Severity.SEVERITY_UNKNOWN, "current_status": Status.STATUS_AFFECTED},
        ]
        mock_obs_objects.filter.return_value.values.return_value = observations

        result = calculate_observation_metrics_for_product(self.product_1)

        self.assertTrue(result)
        self.assertEqual(todays_metrics.active_critical, 1)
        self.assertEqual(todays_metrics.active_high, 1)
        self.assertEqual(todays_metrics.active_medium, 1)
        self.assertEqual(todays_metrics.active_low, 1)
        self.assertEqual(todays_metrics.active_none, 1)
        self.assertEqual(todays_metrics.active_unknown, 1)
        self.assertEqual(todays_metrics.open, 3)
        self.assertEqual(todays_metrics.affected, 2)
        self.assertEqual(todays_metrics.in_review, 1)

    @patch("application.metrics.services.metrics.Observation.objects")
    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    @patch("application.metrics.services.metrics._get_latest_product_metrics")
    @patch("application.metrics.services.metrics.timezone")
    def test_observations_today_with_all_statuses(
        self, mock_timezone, mock_get_latest, mock_pm_objects, mock_obs_objects
    ):
        today = date(2025, 6, 15)
        mock_timezone.localdate.return_value = today
        self.product_1.last_observation_change = datetime(2025, 6, 15, 10, 0, 0)

        mock_get_latest.return_value = None

        todays_metrics = ProductMetricsStub()
        mock_pm_objects.update_or_create.return_value = (todays_metrics, True)

        observations = [
            {"current_severity": Severity.SEVERITY_CRITICAL, "current_status": Status.STATUS_OPEN},
            {"current_severity": Severity.SEVERITY_HIGH, "current_status": Status.STATUS_AFFECTED},
            {"current_severity": Severity.SEVERITY_MEDIUM, "current_status": Status.STATUS_RESOLVED},
            {"current_severity": Severity.SEVERITY_LOW, "current_status": Status.STATUS_DUPLICATE},
            {"current_severity": Severity.SEVERITY_NONE, "current_status": Status.STATUS_FALSE_POSITIVE},
            {"current_severity": Severity.SEVERITY_UNKNOWN, "current_status": Status.STATUS_IN_REVIEW},
            {"current_severity": Severity.SEVERITY_LOW, "current_status": Status.STATUS_NOT_AFFECTED},
            {"current_severity": Severity.SEVERITY_LOW, "current_status": Status.STATUS_NOT_SECURITY},
            {"current_severity": Severity.SEVERITY_LOW, "current_status": Status.STATUS_RISK_ACCEPTED},
        ]
        mock_obs_objects.filter.return_value.values.return_value = observations

        result = calculate_observation_metrics_for_product(self.product_1)

        self.assertTrue(result)
        self.assertEqual(todays_metrics.open, 1)
        self.assertEqual(todays_metrics.affected, 1)
        self.assertEqual(todays_metrics.resolved, 1)
        self.assertEqual(todays_metrics.duplicate, 1)
        self.assertEqual(todays_metrics.false_positive, 1)
        self.assertEqual(todays_metrics.in_review, 1)
        self.assertEqual(todays_metrics.not_affected, 1)
        self.assertEqual(todays_metrics.not_security, 1)
        self.assertEqual(todays_metrics.risk_accepted, 1)
        # Active statuses: Open, Affected, In review
        self.assertEqual(todays_metrics.active_critical, 1)
        self.assertEqual(todays_metrics.active_high, 1)
        self.assertEqual(todays_metrics.active_unknown, 1)
        # Resolved, Duplicate, etc. are not active
        self.assertEqual(todays_metrics.active_medium, 0)
        self.assertEqual(todays_metrics.active_low, 0)

    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    @patch("application.metrics.services.metrics._get_latest_product_metrics")
    @patch("application.metrics.services.metrics.timezone")
    def test_no_changes_today_copies_previous_metrics(self, mock_timezone, mock_get_latest, mock_pm_objects):
        today = date(2025, 6, 15)
        yesterday = date(2025, 6, 14)
        mock_timezone.localdate.return_value = today
        self.product_1.last_observation_change = datetime(2025, 6, 14, 10, 0, 0)

        latest_metrics = ProductMetricsStub(
            date=yesterday,
            active_critical=5,
            active_high=3,
            active_medium=2,
            active_low=1,
            open=4,
            resolved=2,
        )
        mock_get_latest.return_value = latest_metrics

        created_metrics = []
        mock_pm_objects.create.side_effect = lambda **kwargs: created_metrics.append(kwargs)

        result = calculate_observation_metrics_for_product(self.product_1)

        self.assertTrue(result)
        self.assertEqual(len(created_metrics), 1)
        self.assertEqual(created_metrics[0]["date"], today)
        self.assertEqual(created_metrics[0]["active_critical"], 5)
        self.assertEqual(created_metrics[0]["active_high"], 3)
        self.assertEqual(created_metrics[0]["active_medium"], 2)
        self.assertEqual(created_metrics[0]["active_low"], 1)
        self.assertEqual(created_metrics[0]["open"], 4)
        self.assertEqual(created_metrics[0]["resolved"], 2)

    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    @patch("application.metrics.services.metrics._get_latest_product_metrics")
    @patch("application.metrics.services.metrics.timezone")
    def test_no_changes_today_fills_gap_days(self, mock_timezone, mock_get_latest, mock_pm_objects):
        today = date(2025, 6, 15)
        three_days_ago = date(2025, 6, 12)
        mock_timezone.localdate.return_value = today
        self.product_1.last_observation_change = datetime(2025, 6, 12, 10, 0, 0)

        latest_metrics = ProductMetricsStub(date=three_days_ago, active_critical=2, open=1)
        mock_get_latest.return_value = latest_metrics

        created_metrics = []
        mock_pm_objects.create.side_effect = lambda **kwargs: created_metrics.append(kwargs)

        result = calculate_observation_metrics_for_product(self.product_1)

        self.assertTrue(result)
        self.assertEqual(len(created_metrics), 3)
        self.assertEqual(created_metrics[0]["date"], date(2025, 6, 13))
        self.assertEqual(created_metrics[1]["date"], date(2025, 6, 14))
        self.assertEqual(created_metrics[2]["date"], date(2025, 6, 15))
        for m in created_metrics:
            self.assertEqual(m["active_critical"], 2)
            self.assertEqual(m["open"], 1)

    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    @patch("application.metrics.services.metrics._get_latest_product_metrics")
    @patch("application.metrics.services.metrics.timezone")
    def test_no_changes_today_metrics_already_up_to_date(self, mock_timezone, mock_get_latest, mock_pm_objects):
        today = date(2025, 6, 15)
        mock_timezone.localdate.return_value = today
        self.product_1.last_observation_change = datetime(2025, 6, 14, 10, 0, 0)

        latest_metrics = ProductMetricsStub(date=today)
        mock_get_latest.return_value = latest_metrics

        result = calculate_observation_metrics_for_product(self.product_1)

        self.assertFalse(result)
        mock_pm_objects.create.assert_not_called()


class TestGetLatestProductMetrics(BaseTestCase):
    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    def test_returns_latest_metrics(self, mock_pm_objects):
        from application.metrics.services.metrics import (
            _get_latest_product_observation_metrics,
        )

        expected_metrics = ProductMetricsStub(date=date(2025, 6, 15))
        mock_pm_objects.filter.return_value.latest.return_value = expected_metrics

        result = _get_latest_product_observation_metrics(self.product_1)

        self.assertEqual(result, expected_metrics)
        mock_pm_objects.filter.assert_called_once_with(product=self.product_1)
        mock_pm_objects.filter.return_value.latest.assert_called_once_with("date")

    @patch("application.metrics.services.metrics.Product_Metrics.objects")
    def test_returns_none_when_no_metrics(self, mock_pm_objects):
        from application.metrics.models import Product_Metrics
        from application.metrics.services.metrics import (
            _get_latest_product_observation_metrics,
        )

        mock_pm_objects.filter.return_value.latest.side_effect = Product_Metrics.DoesNotExist

        result = _get_latest_product_observation_metrics(self.product_1)

        self.assertIsNone(result)


class TestGetProductMetricsTimeline(BaseTestCase):
    @patch("application.metrics.services.metrics.get_days")
    @patch("application.metrics.services.metrics.get_product_metrics")
    def test_no_product_no_age_filter(self, mock_get_metrics, mock_get_days):
        metrics = [
            ProductMetricsStub(date=date(2025, 6, 14), active_critical=2, open=1),
            ProductMetricsStub(date=date(2025, 6, 15), active_critical=3, open=2),
        ]
        mock_get_metrics.return_value = metrics
        mock_get_days.return_value = None

        result = get_product_metrics_timeline(None, "all")

        self.assertEqual(len(result), 2)
        self.assertEqual(result["2025-06-14"]["active_critical"], 2)
        self.assertEqual(result["2025-06-14"]["open"], 1)
        self.assertEqual(result["2025-06-15"]["active_critical"], 3)
        self.assertEqual(result["2025-06-15"]["open"], 2)

    @patch("application.metrics.services.metrics.get_days")
    @patch("application.metrics.services.metrics.get_product_metrics")
    def test_no_product_aggregates_multiple_products_same_date(self, mock_get_metrics, mock_get_days):
        metrics = [
            ProductMetricsStub(
                date=date(2025, 6, 15),
                active_critical=2,
                active_high=1,
                open=3,
            ),
            ProductMetricsStub(
                date=date(2025, 6, 15),
                active_critical=1,
                active_high=4,
                open=2,
            ),
        ]
        mock_get_metrics.return_value = metrics
        mock_get_days.return_value = None

        result = get_product_metrics_timeline(None, "all")

        self.assertEqual(len(result), 1)
        self.assertEqual(result["2025-06-15"]["active_critical"], 3)
        self.assertEqual(result["2025-06-15"]["active_high"], 5)
        self.assertEqual(result["2025-06-15"]["open"], 5)

    @patch("application.metrics.services.metrics.get_days")
    @patch("application.metrics.services.metrics.get_product_metrics")
    def test_single_product_no_aggregation(self, mock_get_metrics, mock_get_days):
        self.product_1.is_product_group = False
        metrics_qs = QuerySetStub(
            [
                ProductMetricsStub(
                    date=date(2025, 6, 15),
                    active_critical=5,
                    active_high=3,
                    open=2,
                    resolved=1,
                )
            ]
        )
        mock_get_metrics.return_value = metrics_qs
        mock_get_days.return_value = None

        result = get_product_metrics_timeline(self.product_1, "all")

        self.assertEqual(len(result), 1)
        self.assertEqual(result["2025-06-15"]["active_critical"], 5)
        self.assertEqual(result["2025-06-15"]["active_high"], 3)
        self.assertEqual(result["2025-06-15"]["open"], 2)
        self.assertEqual(result["2025-06-15"]["resolved"], 1)
        metrics_qs.assert_filtered_with(self, product=self.product_1)

    @patch("application.metrics.services.metrics.get_days")
    @patch("application.metrics.services.metrics.get_product_metrics")
    def test_product_group_filters_and_aggregates(self, mock_get_metrics, mock_get_days):
        self.product_group_1.is_product_group = True
        metrics_qs = QuerySetStub(
            [
                ProductMetricsStub(
                    date=date(2025, 6, 15),
                    active_critical=2,
                    open=1,
                ),
                ProductMetricsStub(
                    date=date(2025, 6, 15),
                    active_critical=3,
                    open=4,
                ),
            ]
        )
        mock_get_metrics.return_value = metrics_qs
        mock_get_days.return_value = None

        result = get_product_metrics_timeline(self.product_group_1, "all")

        self.assertEqual(result["2025-06-15"]["active_critical"], 5)
        self.assertEqual(result["2025-06-15"]["open"], 5)
        metrics_qs.assert_filtered_with(self, product__product_group=self.product_group_1)

    @patch("application.metrics.services.metrics.timezone")
    @patch("application.metrics.services.metrics.get_days")
    @patch("application.metrics.services.metrics.get_product_metrics")
    def test_age_filter_applied(self, mock_get_metrics, mock_get_days, mock_timezone):
        mock_get_days.return_value = 7

        now = datetime(2025, 6, 15, 14, 30, 0)
        mock_timezone.now.return_value = now

        metrics_qs = QuerySetStub([])
        mock_get_metrics.return_value = metrics_qs

        result = get_product_metrics_timeline(None, "Past 7 days")

        self.assertEqual(result, {})
        expected_threshold = datetime(2025, 6, 8, 0, 0, 0)
        metrics_qs.assert_filtered_with(self, date__gte=expected_threshold)

    @patch("application.metrics.services.metrics.get_days")
    @patch("application.metrics.services.metrics.get_product_metrics")
    def test_empty_metrics(self, mock_get_metrics, mock_get_days):
        mock_get_metrics.return_value = []
        mock_get_days.return_value = None

        result = get_product_metrics_timeline(None, "all")

        self.assertEqual(result, {})


class TestGetProductMetricsCurrent(BaseTestCase):
    @patch("application.metrics.services.metrics.get_todays_product_metrics")
    def test_no_product_no_metrics(self, mock_get_todays):
        mock_get_todays.return_value = QuerySetStub([])

        result = get_product_metrics_current(None)

        expected = _initialize_response_data()
        self.assertEqual(result, expected)

    @patch("application.metrics.services.metrics.get_todays_product_metrics")
    def test_no_product_with_metrics(self, mock_get_todays):
        metrics = [
            ProductMetricsStub(
                active_critical=1,
                active_high=2,
                active_medium=3,
                open=4,
                resolved=5,
            ),
            ProductMetricsStub(
                active_critical=10,
                active_high=20,
                active_medium=30,
                open=40,
                resolved=50,
            ),
        ]
        mock_get_todays.return_value = QuerySetStub(metrics)

        result = get_product_metrics_current(None)

        self.assertEqual(result["active_critical"], 11)
        self.assertEqual(result["active_high"], 22)
        self.assertEqual(result["active_medium"], 33)
        self.assertEqual(result["open"], 44)
        self.assertEqual(result["resolved"], 55)

    @patch("application.metrics.services.metrics.get_todays_product_metrics")
    def test_single_product_filters(self, mock_get_todays):
        self.product_1.is_product_group = False
        metrics = [ProductMetricsStub(active_critical=7, open=3)]
        metrics_qs = QuerySetStub(metrics)
        mock_get_todays.return_value = metrics_qs

        result = get_product_metrics_current(self.product_1)

        self.assertEqual(result["active_critical"], 7)
        self.assertEqual(result["open"], 3)
        metrics_qs.assert_filtered_with(self, product=self.product_1)

    @patch("application.metrics.services.metrics.get_todays_product_metrics")
    def test_product_group_filters(self, mock_get_todays):
        self.product_group_1.is_product_group = True
        metrics = [ProductMetricsStub(active_critical=4, open=2)]
        metrics_qs = QuerySetStub(metrics)
        mock_get_todays.return_value = metrics_qs

        result = get_product_metrics_current(self.product_group_1)

        self.assertEqual(result["active_critical"], 4)
        self.assertEqual(result["open"], 2)
        metrics_qs.assert_filtered_with(self, product__product_group=self.product_group_1)


class TestGetCodechartaMetrics(BaseTestCase):
    @patch("application.metrics.services.metrics.Observation.objects")
    def test_no_observations(self, mock_obs_objects):
        mock_obs_objects.filter.return_value = []

        result = get_codecharta_metrics(self.product_1)

        self.assertEqual(result, [])
        mock_obs_objects.filter.assert_called_once_with(
            product=self.product_1,
            branch=self.product_1.repository_default_branch,
            current_status__in=Status.STATUS_ACTIVE,
        )

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_observation_without_source_file(self, mock_obs_objects):
        obs = ObservationStub(
            origin_source_file="",
            current_severity=Severity.SEVERITY_HIGH,
        )
        mock_obs_objects.filter.return_value = [obs]

        result = get_codecharta_metrics(self.product_1)

        self.assertEqual(result, [])

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_single_observation_critical(self, mock_obs_objects):
        obs = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_CRITICAL,
        )
        mock_obs_objects.filter.return_value = [obs]

        result = get_codecharta_metrics(self.product_1)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["source_file"], "src/main.py")
        self.assertEqual(entry["vulnerabilities_total"], 1)
        self.assertEqual(entry["vulnerabilities_critical"], 1)
        self.assertEqual(entry["vulnerabilities_high"], 0)
        self.assertEqual(entry["vulnerabilities_high_and_above"], 1)
        self.assertEqual(entry["vulnerabilities_medium_and_above"], 1)
        self.assertEqual(entry["vulnerabilities_low_and_above"], 1)

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_single_observation_high(self, mock_obs_objects):
        obs = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_HIGH,
        )
        mock_obs_objects.filter.return_value = [obs]

        result = get_codecharta_metrics(self.product_1)

        entry = result[0]
        self.assertEqual(entry["vulnerabilities_high"], 1)
        self.assertEqual(entry["vulnerabilities_high_and_above"], 1)
        self.assertEqual(entry["vulnerabilities_medium_and_above"], 1)
        self.assertEqual(entry["vulnerabilities_low_and_above"], 1)
        self.assertEqual(entry["vulnerabilities_critical"], 0)

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_single_observation_medium(self, mock_obs_objects):
        obs = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_MEDIUM,
        )
        mock_obs_objects.filter.return_value = [obs]

        result = get_codecharta_metrics(self.product_1)

        entry = result[0]
        self.assertEqual(entry["vulnerabilities_medium"], 1)
        self.assertEqual(entry["vulnerabilities_high_and_above"], 0)
        self.assertEqual(entry["vulnerabilities_medium_and_above"], 1)
        self.assertEqual(entry["vulnerabilities_low_and_above"], 1)

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_single_observation_low(self, mock_obs_objects):
        obs = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_LOW,
        )
        mock_obs_objects.filter.return_value = [obs]

        result = get_codecharta_metrics(self.product_1)

        entry = result[0]
        self.assertEqual(entry["vulnerabilities_low"], 1)
        self.assertEqual(entry["vulnerabilities_high_and_above"], 0)
        self.assertEqual(entry["vulnerabilities_medium_and_above"], 0)
        self.assertEqual(entry["vulnerabilities_low_and_above"], 1)

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_single_observation_none_severity(self, mock_obs_objects):
        obs = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_NONE,
        )
        mock_obs_objects.filter.return_value = [obs]

        result = get_codecharta_metrics(self.product_1)

        entry = result[0]
        self.assertEqual(entry["vulnerabilities_none"], 1)
        self.assertEqual(entry["vulnerabilities_high_and_above"], 0)
        self.assertEqual(entry["vulnerabilities_medium_and_above"], 0)
        self.assertEqual(entry["vulnerabilities_low_and_above"], 0)

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_multiple_observations_same_file(self, mock_obs_objects):
        obs1 = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_CRITICAL,
        )
        obs2 = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_HIGH,
        )
        obs3 = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_MEDIUM,
        )
        mock_obs_objects.filter.return_value = [obs1, obs2, obs3]

        result = get_codecharta_metrics(self.product_1)

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["vulnerabilities_total"], 3)
        self.assertEqual(entry["vulnerabilities_critical"], 1)
        self.assertEqual(entry["vulnerabilities_high"], 1)
        self.assertEqual(entry["vulnerabilities_medium"], 1)
        self.assertEqual(entry["vulnerabilities_high_and_above"], 2)
        self.assertEqual(entry["vulnerabilities_medium_and_above"], 3)
        self.assertEqual(entry["vulnerabilities_low_and_above"], 3)

    @patch("application.metrics.services.metrics.Observation.objects")
    def test_multiple_observations_different_files(self, mock_obs_objects):
        obs1 = ObservationStub(
            origin_source_file="src/main.py",
            current_severity=Severity.SEVERITY_CRITICAL,
        )
        obs2 = ObservationStub(
            origin_source_file="src/utils.py",
            current_severity=Severity.SEVERITY_LOW,
        )
        mock_obs_objects.filter.return_value = [obs1, obs2]

        result = get_codecharta_metrics(self.product_1)

        self.assertEqual(len(result), 2)
        files = {entry["source_file"]: entry for entry in result}
        self.assertEqual(files["src/main.py"]["vulnerabilities_critical"], 1)
        self.assertEqual(files["src/utils.py"]["vulnerabilities_low"], 1)


# --- Stubs ---


class ProductMetricsStatusStub:
    def __init__(self):
        self.last_calculated = None
        self._saved = False

    def save(self):
        self._saved = True


class ProductMetricsStub:
    def __init__(
        self,
        date=None,
        active_critical=0,
        active_high=0,
        active_medium=0,
        active_low=0,
        active_none=0,
        active_unknown=0,
        open=0,
        affected=0,
        resolved=0,
        duplicate=0,
        false_positive=0,
        in_review=0,
        not_affected=0,
        not_security=0,
        risk_accepted=0,
    ):
        self.date = date
        self.active_critical = active_critical
        self.active_high = active_high
        self.active_medium = active_medium
        self.active_low = active_low
        self.active_none = active_none
        self.active_unknown = active_unknown
        self.open = open
        self.affected = affected
        self.resolved = resolved
        self.duplicate = duplicate
        self.false_positive = false_positive
        self.in_review = in_review
        self.not_affected = not_affected
        self.not_security = not_security
        self.risk_accepted = risk_accepted
        self._saved = False

    def save(self):
        self._saved = True

    def assert_save_called(self, test_case):
        test_case.assertTrue(self._saved)


class ObservationStub:
    def __init__(self, origin_source_file="", current_severity=""):
        self.origin_source_file = origin_source_file
        self.current_severity = current_severity


class QuerySetStub:
    """A simple stub that supports filter() chaining and iteration."""

    def __init__(self, items=None):
        self._items = items or []
        self._filter_calls = []

    def filter(self, **kwargs):
        self._filter_calls.append(kwargs)
        return self

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def assert_filtered_with(self, test_case, **expected_kwargs):
        test_case.assertTrue(
            any(kwargs == expected_kwargs for kwargs in self._filter_calls),
            f"Expected filter call with {expected_kwargs}, got {self._filter_calls}",
        )
