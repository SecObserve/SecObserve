from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.commons.models import Settings
from application.core.models import Branch, Observation, Product, Product_Member
from application.core.types import Severity, Status
from application.import_observations.models import Parser
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from application.metrics.models import (
    Product_License_Metrics,
    Product_Metrics,
    Product_Metrics_Status,
)
from application.metrics.services.metrics import (
    _initialize_response_data,
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


class TestCalculateProductMetricsForChangedProducts(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.parser = Parser.objects.create(name="metrics_parser")
        self.product_changed = self._create_product("product_changed")
        self.product_unchanged = self._create_product("product_unchanged")

    def _create_product(self, name: str) -> Product:
        product = Product.objects.create(name=name)
        Branch.objects.create(product=product, name="main", is_default_branch=True)
        product.refresh_from_db()
        return product

    def _create_observation(self, product: Product) -> None:
        # Created without an observation log, which would mark the product as changed
        Observation.objects.create(
            title=f"observation_{Observation.objects.count()}",
            product=product,
            branch=product.repository_default_branch,
            parser=self.parser,
            parser_severity=Severity.SEVERITY_HIGH,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

    def _create_license_component(self, product: Product) -> None:
        # bulk_create doesn't send the post_save signal, which would mark the product as changed
        name = f"component_{License_Component.objects.count()}"
        License_Component.objects.bulk_create(
            [
                License_Component(
                    identity_hash=f"{name:_<64}",
                    product=product,
                    branch=product.repository_default_branch,
                    component_name=name,
                    component_name_version=name,
                    evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
                    numerical_evaluation_result=1,
                )
            ]
        )

    def _mark_as_changed(self, product: Product, last_change: datetime | None = None) -> None:
        last_change = last_change or timezone.now()
        Product.objects.filter(pk=product.pk).update(
            last_observation_change=last_change, last_license_change=last_change
        )

    def _active_high(self, product: Product) -> int:
        return Product_Metrics.objects.get(product=product, date=timezone.localdate()).active_high

    def _forbidden(self, product: Product) -> int:
        return Product_License_Metrics.objects.get(product=product, date=timezone.localdate()).forbidden

    def test_unchanged_product_with_todays_metrics_is_skipped(self):
        calculate_product_metrics()
        self._create_observation(self.product_unchanged)
        self._create_license_component(self.product_unchanged)

        result = calculate_product_metrics()

        self.assertEqual("Calculated metrics for 0 products.", result)
        self.assertEqual(0, self._active_high(self.product_unchanged))
        self.assertEqual(0, self._forbidden(self.product_unchanged))

    def test_product_changed_after_last_run_is_recalculated(self):
        calculate_product_metrics()
        self._create_observation(self.product_changed)
        self._create_license_component(self.product_changed)
        self._create_observation(self.product_unchanged)
        self._mark_as_changed(self.product_changed)

        result = calculate_product_metrics()

        self.assertEqual("Calculated metrics for 1 product.", result)
        self.assertEqual(1, self._active_high(self.product_changed))
        self.assertEqual(1, self._forbidden(self.product_changed))
        self.assertEqual(0, self._active_high(self.product_unchanged))

    def test_product_changed_during_run_is_recalculated_next_run(self):
        load_status = Product_Metrics_Status.load

        def change_after_metrics_of_product_have_been_calculated():
            self._create_observation(self.product_changed)
            self._mark_as_changed(self.product_changed)
            return load_status()

        with patch(
            "application.metrics.services.metrics.Product_Metrics_Status.load",
            side_effect=change_after_metrics_of_product_have_been_calculated,
        ):
            calculate_product_metrics()
        self.assertEqual(0, self._active_high(self.product_changed))

        calculate_product_metrics()

        self.assertEqual(1, self._active_high(self.product_changed))

    def test_change_committed_after_run_with_earlier_timestamp_is_recalculated(self):
        # The transaction of an import can start before a run and commit after it
        before_run = timezone.now() - timedelta(minutes=1)
        calculate_product_metrics()
        self._create_observation(self.product_changed)
        self._mark_as_changed(self.product_changed, before_run)

        calculate_product_metrics()

        self.assertEqual(1, self._active_high(self.product_changed))

    def test_product_without_todays_metrics_is_backfilled(self):
        Product_Metrics.objects.create(
            product=self.product_unchanged,
            date=timezone.localdate() - timedelta(days=2),
            active_high=5,
            last_observation_change=self.product_unchanged.last_observation_change,
        )
        self._create_observation(self.product_unchanged)

        calculate_product_metrics()

        self.assertEqual(5, self._active_high(self.product_unchanged))
        self.assertEqual(3, Product_Metrics.objects.filter(product=self.product_unchanged, active_high=5).count())

    def test_product_without_todays_metrics_changed_after_latest_metrics_is_recalculated(self):
        Product_Metrics.objects.create(
            product=self.product_changed,
            date=timezone.localdate() - timedelta(days=1),
            active_high=5,
            last_observation_change=self.product_changed.last_observation_change - timedelta(minutes=1),
        )
        self._create_observation(self.product_changed)

        calculate_product_metrics()

        self.assertEqual(1, self._active_high(self.product_changed))

    def test_queries_do_not_depend_on_number_of_unchanged_products(self):
        calculate_product_metrics()
        self._mark_as_changed(self.product_changed)
        with CaptureQueriesContext(connection) as queries_2_products:
            calculate_product_metrics()

        for i in range(10):
            self._create_product(f"product_{i}")
        calculate_product_metrics()
        self._mark_as_changed(self.product_changed)
        with CaptureQueriesContext(connection) as queries_12_products:
            calculate_product_metrics()

        self.assertEqual(len(queries_2_products), len(queries_12_products))

    def test_queries_do_not_depend_on_number_of_changed_products(self):
        calculate_product_metrics()
        self._mark_as_changed(self.product_changed)
        with CaptureQueriesContext(connection) as queries_1_changed:
            calculate_product_metrics()

        products = [self._create_product(f"product_{i}") for i in range(10)]
        for product in products:
            self._create_observation(product)
        calculate_product_metrics()
        for product in [self.product_changed, *products]:
            self._mark_as_changed(product)
        with CaptureQueriesContext(connection) as queries_11_changed:
            calculate_product_metrics()

        self.assertEqual(len(queries_1_changed), len(queries_11_changed))
        self.assertEqual(1, self._active_high(products[0]))


class TestCalculateProductMetricsCounts(BaseTestCase):
    def _save_product_with_branches(self) -> tuple[Branch, Branch]:
        parser = Parser.objects.create(name="metrics_parser")
        self.product_1.repository_default_branch = None
        self.product_1.save()
        default_branch = Branch.objects.create(product=self.product_1, name="main", is_default_branch=True)
        other_branch = Branch.objects.create(product=self.product_1, name="feature", is_default_branch=False)
        self.product_1.repository_default_branch = default_branch
        self.product_1.save()
        self.parser_1 = parser
        return default_branch, other_branch

    def _create_observation(self, branch: Branch, severity: str, status: str) -> None:
        Observation.objects.create(
            title=f"{severity}_{status}_{branch.name}",
            product=self.product_1,
            branch=branch,
            parser=self.parser_1,
            parser_severity=severity,
            parser_status=status,
            import_last_seen=timezone.now(),
        )

    def _create_license_component(self, branch: Branch, evaluation_result: str, name: str) -> None:
        License_Component.objects.create(
            identity_hash=f"{name:_<64}"[:64],
            product=self.product_1,
            branch=branch,
            component_name=name,
            component_name_version=name,
            evaluation_result=evaluation_result,
            numerical_evaluation_result=License_Policy_Evaluation_Result.NUMERICAL_RESULTS[evaluation_result],
        )

    def test_observation_metrics_count_default_branch(self):
        default_branch, other_branch = self._save_product_with_branches()
        self._create_observation(default_branch, Severity.SEVERITY_CRITICAL, Status.STATUS_OPEN)
        self._create_observation(default_branch, Severity.SEVERITY_HIGH, Status.STATUS_AFFECTED)
        self._create_observation(default_branch, Severity.SEVERITY_MEDIUM, Status.STATUS_RESOLVED)
        self._create_observation(default_branch, Severity.SEVERITY_UNKNOWN, Status.STATUS_IN_REVIEW)
        self._create_observation(other_branch, Severity.SEVERITY_LOW, Status.STATUS_OPEN)

        calculate_product_metrics()

        metrics = Product_Metrics.objects.get(product=self.product_1, date=timezone.localdate())
        self.assertEqual(1, metrics.active_critical)
        self.assertEqual(1, metrics.active_high)
        self.assertEqual(0, metrics.active_medium)
        self.assertEqual(0, metrics.active_low)
        self.assertEqual(1, metrics.active_unknown)
        self.assertEqual(1, metrics.open)
        self.assertEqual(1, metrics.affected)
        self.assertEqual(1, metrics.resolved)
        self.assertEqual(1, metrics.in_review)

    def test_license_metrics_count_default_branch(self):
        default_branch, other_branch = self._save_product_with_branches()
        self._create_license_component(
            default_branch, License_Policy_Evaluation_Result.RESULT_ALLOWED, "allowed_component"
        )
        self._create_license_component(
            default_branch, License_Policy_Evaluation_Result.RESULT_FORBIDDEN, "forbidden_component"
        )
        self._create_license_component(default_branch, License_Policy_Evaluation_Result.RESULT_IGNORED, "ignored")
        self._create_license_component(
            default_branch, License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED, "review_component"
        )
        self._create_license_component(default_branch, License_Policy_Evaluation_Result.RESULT_UNKNOWN, "unknown")
        self._create_license_component(
            other_branch, License_Policy_Evaluation_Result.RESULT_FORBIDDEN, "other_branch_component"
        )

        calculate_product_metrics()

        metrics = Product_License_Metrics.objects.get(product=self.product_1, date=timezone.localdate())
        self.assertEqual(1, metrics.allowed)
        self.assertEqual(1, metrics.forbidden)
        self.assertEqual(1, metrics.ignored)
        self.assertEqual(1, metrics.review_required)
        self.assertEqual(1, metrics.unknown)

    def test_product_without_default_branch_counts_observations_without_branch(self):
        self.parser_1 = Parser.objects.create(name="metrics_parser")
        self.product_1.repository_default_branch = None
        self.product_1.save()
        branch = Branch.objects.create(product=self.product_1, name="feature")
        for title, observation_branch in (("without_branch", None), ("with_branch", branch)):
            Observation.objects.create(
                title=title,
                product=self.product_1,
                branch=observation_branch,
                parser=self.parser_1,
                parser_severity=Severity.SEVERITY_HIGH,
                parser_status=Status.STATUS_OPEN,
                import_last_seen=timezone.now(),
            )

        calculate_product_metrics()

        metrics = Product_Metrics.objects.get(product=self.product_1, date=timezone.localdate())
        self.assertEqual(1, metrics.active_high)

    def test_product_group_has_no_metrics(self):
        product_group = Product.objects.create(name="product_group", is_product_group=True)

        calculate_product_metrics()

        self.assertFalse(Product_Metrics.objects.filter(product=product_group).exists())
        self.assertFalse(Product_License_Metrics.objects.filter(product=product_group).exists())

    def test_license_metrics_without_license_management(self):
        settings = Settings.load()
        settings.feature_license_management = False
        settings.save()
        self._save_product_with_branches()

        calculate_product_metrics()

        self.assertTrue(Product_Metrics.objects.filter(product=self.product_1).exists())
        self.assertFalse(Product_License_Metrics.objects.exists())


class TestGetProductMetricsTimeline(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_group = Product.objects.create(name="group", is_product_group=True)
        self.product_in_group = Product.objects.create(name="in group", product_group=self.product_group)
        self.product_other = Product.objects.create(name="other")
        self.today = timezone.localdate().isoformat()
        self.month_ago = (timezone.localdate() - timedelta(days=30)).isoformat()
        for product, critical in ((self.product_in_group, 2), (self.product_other, 3)):
            Product_Metrics.objects.create(product=product, date=self.month_ago, active_critical=critical, open=1)
            Product_Metrics.objects.create(product=product, date=self.today, active_critical=critical + 1, open=2)
        self.superuser = User.objects.create(username="superuser", is_superuser=True)

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_all_products_summed_per_date(self, mock_user):
        mock_user.return_value = self.superuser

        with self.assertNumQueries(1):
            result = get_product_metrics_timeline(None, "all")

        dates = list(result)
        self.assertLess(dates.index(self.month_ago), dates.index(self.today))
        self.assertEqual(5, result[self.month_ago]["active_critical"])
        self.assertEqual(7, result[self.today]["active_critical"])
        self.assertEqual(4, result[self.today]["open"])
        self.assertEqual(0, result[self.today]["risk_accepted"])

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_only_permitted_products_are_summed(self, mock_user):
        user = User.objects.create(username="member")
        Product_Member.objects.create(product=self.product_other, user=user, role=Roles.Reader)
        mock_user.return_value = user

        result = get_product_metrics_timeline(None, "all")

        self.assertEqual(4, result[self.today]["active_critical"])

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_product_group(self, mock_user):
        mock_user.return_value = self.superuser

        result = get_product_metrics_timeline(self.product_group, "all")

        self.assertEqual({self.month_ago, self.today}, set(result))
        self.assertEqual(3, result[self.today]["active_critical"])

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_product_with_age(self, mock_user):
        mock_user.return_value = self.superuser

        result = get_product_metrics_timeline(self.product_other, "Past 7 days")

        self.assertEqual({self.today: {**_initialize_response_data(), "active_critical": 4, "open": 2}}, result)

    @override_settings(TIME_ZONE="Asia/Ho_Chi_Minh")
    @patch("django.utils.timezone.now")
    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_age_starts_at_local_date(self, mock_user, mock_now):
        mock_user.return_value = self.superuser
        product = Product.objects.create(name="time zone")
        for day in (7, 8):
            Product_Metrics.objects.create(product=product, date=date(2025, 6, day))
        # Already 2025-06-15 in TIME_ZONE, but still 2025-06-14 in UTC
        mock_now.return_value = datetime(2025, 6, 14, 20, 0, tzinfo=dt_timezone.utc)

        result = get_product_metrics_timeline(product, "Past 7 days")

        self.assertEqual({"2025-06-08"}, set(result))


class TestGetProductMetricsCurrent(BaseTestCase):
    @patch("application.metrics.services.metrics.get_latest_product_metrics")
    def test_no_product_no_metrics(self, mock_get_latest):
        mock_get_latest.return_value = QuerySetStub([])

        result = get_product_metrics_current(None)

        expected = _initialize_response_data()
        self.assertEqual(result, expected)

    @patch("application.metrics.services.metrics.get_latest_product_metrics")
    def test_no_product_with_metrics(self, mock_get_latest):
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
        mock_get_latest.return_value = QuerySetStub(metrics)

        result = get_product_metrics_current(None)

        self.assertEqual(result["active_critical"], 11)
        self.assertEqual(result["active_high"], 22)
        self.assertEqual(result["active_medium"], 33)
        self.assertEqual(result["open"], 44)
        self.assertEqual(result["resolved"], 55)

    @patch("application.metrics.services.metrics.get_latest_product_metrics")
    def test_single_product_filters(self, mock_get_latest):
        self.product_1.is_product_group = False
        metrics = [ProductMetricsStub(active_critical=7, open=3)]
        mock_get_latest.return_value = QuerySetStub(metrics)

        result = get_product_metrics_current(self.product_1)

        self.assertEqual(result["active_critical"], 7)
        self.assertEqual(result["open"], 3)
        mock_get_latest.assert_called_once_with(self.product_1)

    @patch("application.metrics.services.metrics.get_latest_product_metrics")
    def test_product_group_filters(self, mock_get_latest):
        self.product_group_1.is_product_group = True
        metrics = [ProductMetricsStub(active_critical=4, open=2)]
        mock_get_latest.return_value = QuerySetStub(metrics)

        result = get_product_metrics_current(self.product_group_1)

        self.assertEqual(result["active_critical"], 4)
        self.assertEqual(result["open"], 2)
        mock_get_latest.assert_called_once_with(self.product_group_1)

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_latest_metrics_per_product_when_none_for_today(self, mock_user):
        mock_user.return_value = self.user_admin
        today = timezone.localdate()
        product_group = Product.objects.create(name="product_group", is_product_group=True)
        product_yesterday = Product.objects.create(name="product_yesterday", product_group=product_group)
        Product_Metrics.objects.create(product=product_yesterday, date=today - timedelta(days=1), active_high=1, open=2)
        product_today = Product.objects.create(name="product_today", product_group=product_group)
        Product_Metrics.objects.create(product=product_today, date=today - timedelta(days=1), active_high=90, open=90)
        Product_Metrics.objects.create(product=product_today, date=today, active_high=10, open=20)

        result = get_product_metrics_current(product_group)

        self.assertEqual(11, result["active_high"])
        self.assertEqual(22, result["open"])

        result = get_product_metrics_current(product_yesterday)

        self.assertEqual(1, result["active_high"])
        self.assertEqual(2, result["open"])

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_latest_metrics_for_all_products_when_none_for_today(self, mock_user):
        mock_user.return_value = self.user_admin
        # Fixtures loaded by other test classes may leave older metrics behind, which would be counted as well
        Product_Metrics.objects.all().delete()
        today = timezone.localdate()
        product_yesterday = Product.objects.create(name="product_yesterday")
        Product_Metrics.objects.create(product=product_yesterday, date=today - timedelta(days=2), active_high=80)
        Product_Metrics.objects.create(product=product_yesterday, date=today - timedelta(days=1), active_high=1)
        product_today = Product.objects.create(name="product_today")
        Product_Metrics.objects.create(product=product_today, date=today - timedelta(days=1), active_high=90)
        Product_Metrics.objects.create(product=product_today, date=today, active_high=10)
        Product.objects.create(name="product_without_metrics")

        result = get_product_metrics_current(None)

        self.assertEqual(11, result["active_high"])

    @patch("application.metrics.queries.product_metrics.get_current_user")
    def test_latest_metrics_only_for_authorized_products(self, mock_user):
        user = User.objects.create(username="user_metrics@example.com")
        mock_user.return_value = user
        today = timezone.localdate()
        product_member = Product.objects.create(name="product_member")
        Product_Member.objects.create(product=product_member, user=user, role=Roles.Reader)
        Product_Metrics.objects.create(product=product_member, date=today - timedelta(days=1), active_high=1)
        product_group = Product.objects.create(name="product_group", is_product_group=True)
        Product_Member.objects.create(product=product_group, user=user, role=Roles.Reader)
        product_group_member = Product.objects.create(name="product_group_member", product_group=product_group)
        Product_Metrics.objects.create(product=product_group_member, date=today, active_high=10)
        product_not_member = Product.objects.create(name="product_not_member")
        Product_Metrics.objects.create(product=product_not_member, date=today - timedelta(days=1), active_high=100)

        result = get_product_metrics_current(None)

        self.assertEqual(11, result["active_high"])

        result = get_product_metrics_current(product_not_member)

        self.assertEqual(0, result["active_high"])


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


class ProductMetricsStub:
    def __init__(
        self,
        date=None,
        last_observation_change=None,
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
        self.last_observation_change = last_observation_change
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
    """A simple stub that supports iteration and len()."""

    def __init__(self, items=None):
        self._items = items or []

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)
