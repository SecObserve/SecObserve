from datetime import date
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone

from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from application.core.models import (
    Branch,
    Observation,
    Product,
    Product_Authorization_Group_Member,
)
from application.core.queries.product import get_products
from application.core.types import Severity, Status
from application.import_observations.models import Parser
from application.metrics.models import Product_License_Metrics, Product_Metrics
from unittests.base_test_case import BaseTestCase


class TestGetProducts(BaseTestCase):
    patch.TEST_PREFIX = (
        "test",
        "setUp",
    )

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def _get_product_names(self, products):
        return set(products.values_list("name", flat=True))

    def _create_observation(self, product, branch, severity):
        parser = Parser.objects.first()
        return Observation.objects.create(
            title=f"obs_{severity}",
            product=product,
            branch=branch,
            parser=parser,
            parser_severity=severity,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

    # --- No user ---

    @patch("application.core.queries.product.get_current_user")
    def test_no_user_no_filter(self, mock_user):
        mock_user.return_value = None

        self.assertEqual(0, len(get_products()))

    @patch("application.core.queries.product.get_current_user")
    def test_no_user_is_product_group_false(self, mock_user):
        mock_user.return_value = None

        self.assertEqual(0, len(get_products(is_product_group=False)))

    @patch("application.core.queries.product.get_current_user")
    def test_no_user_is_product_group_true(self, mock_user):
        mock_user.return_value = None

        self.assertEqual(0, len(get_products(is_product_group=True)))

    @patch("application.core.queries.product.get_current_user")
    def test_no_user_with_observation_annotations(self, mock_user):
        mock_user.return_value = None

        self.assertEqual(0, len(get_products(is_product_group=False, with_observation_annotations=True)))

    @patch("application.core.queries.product.get_current_user")
    def test_no_user_with_metrics_annotations(self, mock_user):
        mock_user.return_value = None

        self.assertEqual(0, len(get_products(is_product_group=False, with_metrics_annotations=True)))

    # --- Superuser, is_product_group variations ---

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_no_filter(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")

        products = get_products()

        self.assertEqual(4, len(products))

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_false(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")

        products = get_products(is_product_group=False)

        self.assertEqual(
            {"db_product_internal", "db_product_external"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_true(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")

        products = get_products(is_product_group=True)

        self.assertEqual(
            {"db_product_group", "db_product_group_admin_only"},
            self._get_product_names(products),
        )

    # --- Superuser, with_observation_annotations ---

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_false_with_observation_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")
        product = Product.objects.get(name="db_product_internal")
        branch = Branch.objects.get(product=product, is_default_branch=True)
        self._create_observation(product, branch, Severity.SEVERITY_CRITICAL)
        self._create_observation(product, branch, Severity.SEVERITY_HIGH)

        products = get_products(is_product_group=False, with_observation_annotations=True)

        self.assertEqual(
            {"db_product_internal", "db_product_external"},
            self._get_product_names(products),
        )
        product_internal = products.get(name="db_product_internal")
        self.assertEqual(1, product_internal.active_critical_observation_count)
        self.assertEqual(1, product_internal.active_high_observation_count)
        self.assertEqual(0, product_internal.active_medium_observation_count)
        self.assertEqual(0, product_internal.active_low_observation_count)
        self.assertEqual(0, product_internal.active_none_observation_count)
        self.assertEqual(0, product_internal.active_unknown_observation_count)

        product_external = products.get(name="db_product_external")
        self.assertEqual(0, product_external.active_critical_observation_count)

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_true_with_observation_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")
        product = Product.objects.get(name="db_product_internal")
        branch = Branch.objects.get(product=product, is_default_branch=True)
        self._create_observation(product, branch, Severity.SEVERITY_CRITICAL)

        products = get_products(is_product_group=True, with_observation_annotations=True)

        self.assertEqual(
            {"db_product_group", "db_product_group_admin_only"},
            self._get_product_names(products),
        )
        product_group = products.get(name="db_product_group")
        self.assertEqual(1, product_group.active_critical_observation_count)

        product_group_admin = products.get(name="db_product_group_admin_only")
        self.assertEqual(0, product_group_admin.active_critical_observation_count)

    # --- Superuser, with_metrics_annotations ---

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_false_with_metrics_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")
        product = Product.objects.get(name="db_product_internal")
        Product_Metrics.objects.create(
            product=product,
            date=date.today(),
            active_critical=10,
            active_high=20,
            active_medium=30,
            active_low=40,
            active_none=50,
            active_unknown=60,
        )

        products = get_products(is_product_group=False, with_metrics_annotations=True)

        self.assertEqual(
            {"db_product_internal", "db_product_external"},
            self._get_product_names(products),
        )
        product_internal = products.get(name="db_product_internal")
        self.assertEqual(10, product_internal.active_critical_observation_count)
        self.assertEqual(20, product_internal.active_high_observation_count)
        self.assertEqual(30, product_internal.active_medium_observation_count)
        self.assertEqual(40, product_internal.active_low_observation_count)
        self.assertEqual(50, product_internal.active_none_observation_count)
        self.assertEqual(60, product_internal.active_unknown_observation_count)

        product_external = products.get(name="db_product_external")
        self.assertEqual(0, product_external.active_critical_observation_count)

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_true_with_metrics_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")
        product = Product.objects.get(name="db_product_internal")
        Product_Metrics.objects.create(
            product=product,
            date=date.today(),
            active_critical=5,
            active_high=15,
        )

        products = get_products(is_product_group=True, with_metrics_annotations=True)

        product_group = products.get(name="db_product_group")
        self.assertEqual(5, product_group.active_critical_observation_count)
        self.assertEqual(15, product_group.active_high_observation_count)

        product_group_admin = products.get(name="db_product_group_admin_only")
        self.assertEqual(0, product_group_admin.active_critical_observation_count)

    # --- Superuser, annotation params ignored when is_product_group is None ---

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_no_filter_with_observation_annotations_ignored(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")

        products = get_products(with_observation_annotations=True)

        # All products returned, annotations params are ignored when is_product_group is None
        self.assertEqual(4, len(products))

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_no_filter_with_metrics_annotations_ignored(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")

        products = get_products(with_metrics_annotations=True)

        self.assertEqual(4, len(products))

    # --- Superuser, with_license_metrics_annotations ---

    @patch("application.core.queries.product.get_current_user")
    def test_superuser_is_product_group_false_with_license_metrics_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")
        product = Product.objects.get(name="db_product_internal")
        Product_Metrics.objects.create(
            product=product,
            date=date.today(),
        )
        Product_License_Metrics.objects.create(
            product=product,
            date=date.today(),
            forbidden=3,
            review_required=5,
            unknown=7,
            allowed=11,
            ignored=13,
        )

        products = get_products(is_product_group=False, with_metrics_annotations=True)

        product_internal = products.get(name="db_product_internal")
        self.assertEqual(3, product_internal.forbidden_licenses_count)
        self.assertEqual(5, product_internal.review_required_licenses_count)
        self.assertEqual(7, product_internal.unknown_licenses_count)
        self.assertEqual(11, product_internal.allowed_licenses_count)
        self.assertEqual(13, product_internal.ignored_licenses_count)

    # --- Regular user, direct product member ---

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_direct_member_no_filter(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_write")

        products = get_products()

        self.assertEqual({"db_product_internal"}, self._get_product_names(products))

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_direct_member_is_product_group_false(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_write")

        products = get_products(is_product_group=False)

        self.assertEqual({"db_product_internal"}, self._get_product_names(products))

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_direct_member_is_product_group_true(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_write")

        products = get_products(is_product_group=True)

        self.assertEqual(0, len(products))

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_direct_member_with_observation_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_write")
        product = Product.objects.get(name="db_product_internal")
        branch = Branch.objects.get(product=product, is_default_branch=True)
        self._create_observation(product, branch, Severity.SEVERITY_CRITICAL)

        products = get_products(is_product_group=False, with_observation_annotations=True)

        self.assertEqual({"db_product_internal"}, self._get_product_names(products))
        product_result = products.get(name="db_product_internal")
        self.assertEqual(1, product_result.active_critical_observation_count)

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_direct_member_with_metrics_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_write")
        product = Product.objects.get(name="db_product_internal")
        Product_Metrics.objects.create(
            product=product,
            date=date.today(),
            active_critical=8,
        )

        products = get_products(is_product_group=False, with_metrics_annotations=True)

        self.assertEqual({"db_product_internal"}, self._get_product_names(products))
        product_result = products.get(name="db_product_internal")
        self.assertEqual(8, product_result.active_critical_observation_count)

    # --- Regular user, multiple direct memberships ---

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_multiple_memberships_no_filter(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_read")

        products = get_products()

        self.assertEqual(
            {"db_product_internal", "db_product_external"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_multiple_memberships_is_product_group_false(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_read")

        products = get_products(is_product_group=False)

        self.assertEqual(
            {"db_product_internal", "db_product_external"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_regular_user_multiple_memberships_is_product_group_true(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_internal_read")

        products = get_products(is_product_group=True)

        self.assertEqual(0, len(products))

    # --- Regular user, product group member ---

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_member_no_filter(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_product_group_user")

        products = get_products()

        # Sees product_group (direct member) and product_internal (child of group)
        self.assertEqual(
            {"db_product_group", "db_product_internal"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_member_is_product_group_false(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_product_group_user")

        products = get_products(is_product_group=False)

        self.assertEqual({"db_product_internal"}, self._get_product_names(products))

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_member_is_product_group_true(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_product_group_user")

        products = get_products(is_product_group=True)

        self.assertEqual({"db_product_group"}, self._get_product_names(products))

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_member_is_product_group_false_with_observation_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_product_group_user")
        product = Product.objects.get(name="db_product_internal")
        branch = Branch.objects.get(product=product, is_default_branch=True)
        self._create_observation(product, branch, Severity.SEVERITY_HIGH)

        products = get_products(is_product_group=False, with_observation_annotations=True)

        self.assertEqual({"db_product_internal"}, self._get_product_names(products))
        product_result = products.get(name="db_product_internal")
        self.assertEqual(1, product_result.active_high_observation_count)

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_member_is_product_group_true_with_metrics_annotations(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_product_group_user")
        product = Product.objects.get(name="db_product_internal")
        Product_Metrics.objects.create(
            product=product,
            date=date.today(),
            active_critical=12,
        )

        products = get_products(is_product_group=True, with_metrics_annotations=True)

        self.assertEqual({"db_product_group"}, self._get_product_names(products))
        product_group = products.get(name="db_product_group")
        self.assertEqual(12, product_group.active_critical_observation_count)

    # --- Regular user, authorization group member ---

    @patch("application.core.queries.product.get_current_user")
    def test_authorization_group_member_no_filter(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_auth_group")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product = Product.objects.get(name="db_product_internal")
        Product_Authorization_Group_Member.objects.create(product=product, authorization_group=auth_group, role=1)

        products = get_products()

        # db_product_external (direct member) + db_product_internal (via auth group)
        self.assertEqual(
            {"db_product_external", "db_product_internal"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_authorization_group_member_is_product_group_false(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_auth_group_filter")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product = Product.objects.get(name="db_product_internal")
        Product_Authorization_Group_Member.objects.create(product=product, authorization_group=auth_group, role=1)

        products = get_products(is_product_group=False)

        self.assertEqual(
            {"db_product_external", "db_product_internal"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_authorization_group_member_with_observation_annotations(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_auth_group_obs")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product = Product.objects.get(name="db_product_internal")
        Product_Authorization_Group_Member.objects.create(product=product, authorization_group=auth_group, role=1)
        branch = Branch.objects.get(product=product, is_default_branch=True)
        self._create_observation(product, branch, Severity.SEVERITY_MEDIUM)

        products = get_products(is_product_group=False, with_observation_annotations=True)

        product_result = products.get(name="db_product_internal")
        self.assertEqual(1, product_result.active_medium_observation_count)

    # --- Regular user, product group authorization group member ---

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_authorization_group_member_no_filter(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_pg_auth_group")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product_group = Product.objects.get(name="db_product_group")
        Product_Authorization_Group_Member.objects.create(product=product_group, authorization_group=auth_group, role=1)

        products = get_products()

        # db_product_external (direct member), db_product_group (auth group member),
        # db_product_internal (child of product_group via auth group)
        self.assertEqual(
            {"db_product_external", "db_product_group", "db_product_internal"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_authorization_group_member_is_product_group_false(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_pg_auth_group_filter")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product_group = Product.objects.get(name="db_product_group")
        Product_Authorization_Group_Member.objects.create(product=product_group, authorization_group=auth_group, role=1)

        products = get_products(is_product_group=False)

        self.assertEqual(
            {"db_product_external", "db_product_internal"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_authorization_group_member_is_product_group_true(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_pg_auth_group_true")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product_group = Product.objects.get(name="db_product_group")
        Product_Authorization_Group_Member.objects.create(product=product_group, authorization_group=auth_group, role=1)

        products = get_products(is_product_group=True)

        self.assertEqual(
            {"db_product_group"},
            self._get_product_names(products),
        )

    @patch("application.core.queries.product.get_current_user")
    def test_product_group_authorization_group_member_with_metrics_annotations(self, mock_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user

        auth_group = Authorization_Group.objects.create(name="test_pg_auth_group_metrics")
        Authorization_Group_Member.objects.create(authorization_group=auth_group, user=user, is_manager=False)
        product_group = Product.objects.get(name="db_product_group")
        Product_Authorization_Group_Member.objects.create(product=product_group, authorization_group=auth_group, role=1)
        product = Product.objects.get(name="db_product_internal")
        Product_Metrics.objects.create(
            product=product,
            date=date.today(),
            active_low=25,
        )

        products = get_products(is_product_group=False, with_metrics_annotations=True)

        product_result = products.get(name="db_product_internal")
        self.assertEqual(25, product_result.active_low_observation_count)

    # --- Regular user, no membership ---

    @patch("application.core.queries.product.get_current_user")
    def test_no_membership_no_filter(self, mock_user):
        user = User.objects.create(username="no_membership_user", is_superuser=False)
        mock_user.return_value = user

        self.assertEqual(0, len(get_products()))

    @patch("application.core.queries.product.get_current_user")
    def test_no_membership_is_product_group_false(self, mock_user):
        user = User.objects.create(username="no_membership_user_false", is_superuser=False)
        mock_user.return_value = user

        self.assertEqual(0, len(get_products(is_product_group=False)))

    @patch("application.core.queries.product.get_current_user")
    def test_no_membership_is_product_group_true(self, mock_user):
        user = User.objects.create(username="no_membership_user_true", is_superuser=False)
        mock_user.return_value = user

        self.assertEqual(0, len(get_products(is_product_group=True)))

    @patch("application.core.queries.product.get_current_user")
    def test_no_membership_with_observation_annotations(self, mock_user):
        user = User.objects.create(username="no_membership_user_obs", is_superuser=False)
        mock_user.return_value = user

        self.assertEqual(0, len(get_products(is_product_group=False, with_observation_annotations=True)))

    @patch("application.core.queries.product.get_current_user")
    def test_no_membership_with_metrics_annotations(self, mock_user):
        user = User.objects.create(username="no_membership_user_met", is_superuser=False)
        mock_user.return_value = user

        self.assertEqual(0, len(get_products(is_product_group=False, with_metrics_annotations=True)))
