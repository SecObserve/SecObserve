from unittest.mock import patch

from rest_framework.serializers import ValidationError

from application.access_control.models import Authorization_Group
from application.authorization.services.roles_permissions import Permissions, Roles
from application.commons.models import Settings
from application.core.api.serializers_product import (
    BranchSerializer,
    ProductAuthorizationGroupMemberSerializer,
    ProductMemberSerializer,
    ProductSerializer,
)
from application.core.models import Product
from application.core.types import Severity, Status
from unittests.base_test_case import BaseTestCase


class TestBranchSerializer(BaseTestCase):
    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    @patch("application.core.api.serializers_product.get_permissions_for_role")
    def test_get_permissions_user(self, mock_permissions, mock_highest_user_role, mock_user):
        mock_permissions.return_value = [Permissions.Product_View]
        mock_highest_user_role.return_value = Roles.Writer
        mock_user.return_value = self.user_internal
        product_serializer = ProductSerializer()
        self.assertEqual(
            [Permissions.Product_View],
            product_serializer.get_permissions(obj=self.product_1),
        )
        mock_highest_user_role.assert_called_with(self.product_1)
        mock_permissions.assert_called_with(Roles.Writer)

    @patch("application.core.api.serializers_product.get_product_member")
    def test_validate_security_gate_active_empty(self, mock_product_member):
        product = Product()
        product.security_gate_active = True
        product.security_gate_threshold_critical = None
        product.security_gate_threshold_high = None
        product.security_gate_threshold_medium = None
        product.security_gate_threshold_low = None
        product.security_gate_threshold_none = None
        product.security_gate_threshold_unknown = None
        product.save()

        product_serializer = ProductSerializer(product)
        data = product_serializer.validate(product_serializer.data)

        settings = Settings.load()
        self.assertEqual(settings.security_gate_threshold_critical, data["security_gate_threshold_critical"])
        self.assertEqual(settings.security_gate_threshold_high, data["security_gate_threshold_high"])
        self.assertEqual(settings.security_gate_threshold_medium, data["security_gate_threshold_medium"])
        self.assertEqual(settings.security_gate_threshold_low, data["security_gate_threshold_low"])
        self.assertEqual(settings.security_gate_threshold_none, data["security_gate_threshold_none"])
        self.assertEqual(settings.security_gate_threshold_unknown, data["security_gate_threshold_unknown"])

    @patch("application.core.api.serializers_product.get_product_member")
    def test_validate_security_gate_active_full(self, mock_product_member):
        product = Product()
        product.security_gate_active = True
        product.security_gate_threshold_critical = 1
        product.security_gate_threshold_high = 2
        product.security_gate_threshold_medium = 3
        product.security_gate_threshold_low = 4
        product.security_gate_threshold_none = 5
        product.security_gate_threshold_unknown = 6
        product.save()

        product_serializer = ProductSerializer(product)
        data = product_serializer.validate(product_serializer.data)

        self.assertEqual(1, data["security_gate_threshold_critical"])
        self.assertEqual(2, data["security_gate_threshold_high"])
        self.assertEqual(3, data["security_gate_threshold_medium"])
        self.assertEqual(4, data["security_gate_threshold_low"])
        self.assertEqual(5, data["security_gate_threshold_none"])
        self.assertEqual(6, data["security_gate_threshold_unknown"])

    def test_validate_repository_prefix_empty(self):
        product = Product()
        product.name = "Test Product"
        product.repository_prefix = ""
        product.save()

        product_serializer = ProductSerializer(product)
        validated_data = product_serializer.run_validation(product_serializer.data)

        self.assertEqual("", validated_data["repository_prefix"])

    def test_validate_repository_prefix_invalid(self):
        product = Product()
        product.name = "Test Product"
        product.repository_prefix = "invalid_url"
        product.save()

        product_serializer = ProductSerializer(product)
        with self.assertRaises(ValidationError) as e:
            product_serializer.run_validation(product_serializer.data)

        self.assertEqual(
            "{'repository_prefix': [ErrorDetail(string='Not a valid URL', code='invalid')]}",
            str(e.exception),
        )

    def test_validate_repository_prefix_valid(self):
        product = Product()
        product.name = "Test Product"
        product.repository_prefix = "https://example.com"
        product.save()

        product_serializer = ProductSerializer(product)
        validated_data = product_serializer.run_validation(product_serializer.data)

        self.assertEqual("https://example.com", validated_data["repository_prefix"])

    def test_validate_notification_msteams_slack_invalid(self):
        product = Product()
        product.name = "Test Product"
        product.notification_ms_teams_webhook = "invalid_url"
        product.notification_slack_webhook = "invalid_url"
        product.save()

        product_serializer = ProductSerializer(product)
        with self.assertRaises(ValidationError) as e:
            product_serializer.run_validation(product_serializer.data)

        self.assertEqual(
            "{'notification_ms_teams_webhook': [ErrorDetail(string='Not a valid URL', code='invalid')], 'notification_slack_webhook': [ErrorDetail(string='Not a valid URL', code='invalid')]}",
            str(e.exception),
        )


class TestProductMemberSerializer(BaseTestCase):
    def test_validate_product_change(self):
        product_2 = Product(name="product_2")
        product_member_serializer = ProductMemberSerializer(self.product_member_1)
        attrs = {
            "product": product_2,
        }

        with self.assertRaises(ValidationError) as e:
            product_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Product and user cannot be changed', code='invalid')]",
            str(e.exception),
        )

    def test_validate_user_change(self):
        product_member_serializer = ProductMemberSerializer(self.product_member_1)
        attrs = {
            "user": self.user_external,
        }

        with self.assertRaises(ValidationError) as e:
            product_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Product and user cannot be changed', code='invalid')]",
            str(e.exception),
        )

    @patch("application.core.api.serializers_product.get_product_member")
    def test_validate_already_exists(self, mock_product_member):
        mock_product_member.return_value = self.product_member_1
        product_member_serializer = ProductMemberSerializer()
        attrs = {
            "product": self.product_1,
            "user": self.user_internal,
        }

        with self.assertRaises(ValidationError) as e:
            product_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Product member product_1 / user_internal@example.com already exists', code='invalid')]",
            str(e.exception),
        )
        mock_product_member.assert_called_with(self.product_1, self.user_internal)

    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_add_owner_not_permitted(self, mock_highest_user_role, mock_user):
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_external
        product_member_serializer = ProductMemberSerializer(self.product_member_1)
        attrs = {"role": Roles.Owner}

        with self.assertRaises(ValidationError) as e:
            product_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='You are not permitted to add a member as Owner', code='invalid')]",
            str(e.exception),
        )
        mock_highest_user_role.assert_called_with(self.product_1, self.user_external)
        mock_user.assert_called_once()

    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_change_owner_not_permitted(self, mock_highest_user_role, mock_user):
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_external
        self.product_member_1.role = Roles.Owner
        product_member_serializer = ProductMemberSerializer(self.product_member_1)
        attrs = {"role": Roles.Writer}

        with self.assertRaises(ValidationError) as e:
            product_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='You are not permitted to change the Owner role', code='invalid')]",
            str(e.exception),
        )
        mock_highest_user_role.assert_called_with(self.product_1, self.user_external)
        mock_user.assert_called_once()

    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_successful_with_instance(self, mock_highest_user_role, mock_user):
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_internal
        product_member_serializer = ProductMemberSerializer(self.product_member_1)
        attrs = {"role": Roles.Writer}

        new_attrs = product_member_serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)
        mock_highest_user_role.assert_called_with(self.product_1, self.user_internal)
        mock_user.assert_called_once()

    @patch("application.core.api.serializers_product.get_product_member")
    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_successful_no_instance(self, mock_highest_user_role, mock_user, mock_product_member):
        mock_product_member.return_value = None
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_internal
        product_member_serializer = ProductMemberSerializer()
        attrs = {
            "product": self.product_1,
            "user": self.user_external,
            "role": Roles.Writer,
        }

        new_attrs = product_member_serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)
        mock_product_member.assert_called_with(self.product_1, self.user_external)
        mock_highest_user_role.assert_called_with(self.product_1, self.user_internal)
        mock_user.assert_called_once()


class TestProductAuthorizationGroupMemberSerializer(BaseTestCase):
    def test_validate_product_change(self):
        product_2 = Product(name="product_2")
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer(
            self.product_authorization_group_member_1
        )
        attrs = {
            "product": product_2,
        }

        with self.assertRaises(ValidationError) as e:
            product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Product and authorization group cannot be changed', code='invalid')]",
            str(e.exception),
        )

    def test_validate_authorization_group_change(self):
        authorization_group_1 = Authorization_Group(name="authorization_group_2")
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer(
            self.product_authorization_group_member_1
        )
        attrs = {
            "authorization_group": authorization_group_1,
        }

        with self.assertRaises(ValidationError) as e:
            product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Product and authorization group cannot be changed', code='invalid')]",
            str(e.exception),
        )

    @patch("application.core.api.serializers_product.get_product_authorization_group_member")
    def test_validate_already_exists(self, mock_product_authorization_group_member):
        mock_product_authorization_group_member.return_value = self.product_authorization_group_member_1
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer()
        attrs = {
            "product": self.product_1,
            "authorization_group": self.authorization_group_1,
        }

        with self.assertRaises(ValidationError) as e:
            product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Product authorization group member product_1 / authorization_group_1 already exists', code='invalid')]",
            str(e.exception),
        )
        mock_product_authorization_group_member.assert_called_with(self.product_1, self.authorization_group_1)

    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_add_owner_not_permitted(self, mock_highest_user_role, mock_user):
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_external
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer(
            self.product_authorization_group_member_1
        )
        attrs = {"role": Roles.Owner}

        with self.assertRaises(ValidationError) as e:
            product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='You are not permitted to add a member as Owner', code='invalid')]",
            str(e.exception),
        )
        mock_highest_user_role.assert_called_with(self.product_1, self.user_external)
        mock_user.assert_called_once()

    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_change_owner_not_permitted(self, mock_highest_user_role, mock_user):
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_external
        self.product_authorization_group_member_1.role = Roles.Owner
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer(
            self.product_authorization_group_member_1
        )
        attrs = {"role": Roles.Writer}

        with self.assertRaises(ValidationError) as e:
            product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='You are not permitted to change the Owner role', code='invalid')]",
            str(e.exception),
        )
        mock_highest_user_role.assert_called_with(self.product_1, self.user_external)
        mock_user.assert_called_once()

    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_successful_with_instance(self, mock_highest_user_role, mock_user):
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_internal
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer(
            self.product_authorization_group_member_1
        )
        attrs = {"role": Roles.Writer}

        new_attrs = product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)
        mock_highest_user_role.assert_called_with(self.product_1, self.user_internal)
        mock_user.assert_called_once()

    @patch("application.core.api.serializers_product.get_product_authorization_group_member")
    @patch("application.core.api.serializers_product.get_current_user")
    @patch("application.core.api.serializers_product.get_highest_user_role")
    def test_validate_successful_no_instance(
        self, mock_highest_user_role, mock_user, mock_product_authorization_group_member
    ):
        mock_product_authorization_group_member.return_value = None
        mock_highest_user_role.return_value = Roles.Maintainer
        mock_user.return_value = self.user_internal
        product_authorization_group_member_serializer = ProductAuthorizationGroupMemberSerializer()
        attrs = {
            "product": self.product_1,
            "authorization_group": self.authorization_group_1,
            "role": Roles.Writer,
        }

        new_attrs = product_authorization_group_member_serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)
        mock_product_authorization_group_member.assert_called_with(self.product_1, self.authorization_group_1)
        mock_highest_user_role.assert_called_with(self.product_1, self.user_internal)
        mock_user.assert_called_once()
