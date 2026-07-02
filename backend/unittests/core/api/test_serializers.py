from unittest.mock import Mock, call, patch

from rest_framework.serializers import ValidationError

from application.access_control.models import Authorization_Group
from application.authorization.services.roles_permissions import Permissions, Roles
from application.commons.models import Settings
from application.core.api.serializers_observation import (
    ObservationLogApprovalSerializer,
    ObservationLogBulkApprovalSerializer,
    _get_origin_cloud_resource_url,
)
from application.core.api.serializers_product import (
    BranchSerializer,
    ProductAuthorizationGroupMemberSerializer,
    ProductMemberSerializer,
    ProductSerializer,
)
from application.core.models import Observation, Product
from application.core.types import Assessment_Status, Severity, Status
from unittests.base_test_case import BaseTestCase


class TestProductSerializer(BaseTestCase):
    @patch("application.core.api.serializers_product.user_has_permission")
    def test_issue_tracker_api_key_hidden_without_edit(self, mock_permissions):
        self.product_1.issue_tracker_api_key = "secret-token"
        self.product_1.repository_default_branch = None
        self.product_1.save()

        mock_permissions.return_value = False
        data = ProductSerializer(self.product_1).data
        self.assertNotIn("issue_tracker_api_key", data)

        mock_permissions.return_value = True
        data = ProductSerializer(self.product_1).data
        self.assertEqual("secret-token", data["issue_tracker_api_key"])
        mock_permissions.assert_has_calls(
            [call(self.product_1, Permissions.Product_Edit), call(self.product_1, Permissions.Product_Edit)]
        )


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


class TestObservationSerializer(BaseTestCase):
    def test_github_repository_url_generation(self):
        """Test that GitHub repository URLs are generated correctly"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "github"
        observation.origin_cloud_account_subscription_project = "owner/repo"
        observation.origin_cloud_resource = "my-repo"
        observation.origin_cloud_resource_type = "githubrepository"

        result = _get_origin_cloud_resource_url(observation)
        expected = "https://github.com/owner/repo/my-repo"
        self.assertEqual(result, expected)

    def test_github_organization_url_generation(self):
        """Test that GitHub organization URLs are generated correctly"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "github"
        observation.origin_cloud_account_subscription_project = "owner/repo"
        observation.origin_cloud_resource = "my-org"
        observation.origin_cloud_resource_type = "githuborganization"

        result = _get_origin_cloud_resource_url(observation)
        expected = "https://github.com/my-org"
        self.assertEqual(result, expected)

    def test_case_insensitive_provider(self):
        """Test that provider name is case insensitive"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "GITHUB"
        observation.origin_cloud_account_subscription_project = "owner/repo"
        observation.origin_cloud_resource = "my-repo"
        observation.origin_cloud_resource_type = "githubrepository"

        result = _get_origin_cloud_resource_url(observation)
        expected = "https://github.com/owner/repo/my-repo"
        self.assertEqual(result, expected)

    def test_case_insensitive_resource_type(self):
        """Test that resource type is case insensitive"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "github"
        observation.origin_cloud_account_subscription_project = "owner/repo"
        observation.origin_cloud_resource = "my-repo"
        observation.origin_cloud_resource_type = "GITHUBREPOSITORY"

        result = _get_origin_cloud_resource_url(observation)
        expected = "https://github.com/owner/repo/my-repo"
        self.assertEqual(result, expected)

    def test_non_github_provider_returns_none(self):
        """Test that non-GitHub providers return None"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "aws"
        observation.origin_cloud_account_subscription_project = "account"
        observation.origin_cloud_resource = "resource"
        observation.origin_cloud_resource_type = "githubrepository"

        result = _get_origin_cloud_resource_url(observation)
        self.assertIsNone(result)

    def test_missing_account_subscription_project_returns_none(self):
        """Test that missing account/subscription/project returns None"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "github"
        observation.origin_cloud_account_subscription_project = None
        observation.origin_cloud_resource = "resource"
        observation.origin_cloud_resource_type = "githubrepository"

        result = _get_origin_cloud_resource_url(observation)
        self.assertIsNone(result)

    def test_missing_resource_returns_none(self):
        """Test that missing resource returns None"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "github"
        observation.origin_cloud_account_subscription_project = "account"
        observation.origin_cloud_resource = None
        observation.origin_cloud_resource_type = "githubrepository"

        result = _get_origin_cloud_resource_url(observation)
        self.assertIsNone(result)

    def test_unsupported_resource_type_returns_none(self):
        """Test that unsupported resource types return None"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = "github"
        observation.origin_cloud_account_subscription_project = "account"
        observation.origin_cloud_resource = "resource"
        observation.origin_cloud_resource_type = "unsupportedtype"

        result = _get_origin_cloud_resource_url(observation)
        self.assertIsNone(result)

    def test_empty_strings_returns_none(self):
        """Test that empty strings return None"""
        observation = Mock(spec=Observation)
        observation.origin_cloud_provider = ""
        observation.origin_cloud_account_subscription_project = ""
        observation.origin_cloud_resource = ""
        observation.origin_cloud_resource_type = ""

        result = _get_origin_cloud_resource_url(observation)
        self.assertIsNone(result)


class TestObservationLogApprovalSerializer(BaseTestCase):
    """Tests for the validate method of ObservationLogApprovalSerializer"""

    def _get_serializer_data(self, **kwargs):
        """Helper to create consistent test data with sensible defaults"""
        # Default: Valid Approval
        data = {
            "assessment_status": Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            "comment": "Test comment",  # Serializer expects 'comment' as required in Meta/fields if needed,
            # but here we focus on the specific validation logic.
            # Note: The serializer definition shows 'comment' is required=True.
        }
        data.update(kwargs)
        return data

    def test_valid_approval_no_remark(self):
        """Test that valid approval without rejection remark passes validation"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            rejection_remark="",  # Empty string is allowed for approvals
            observation_log_comment="",
        )
        serializer = ObservationLogApprovalSerializer(data=data)
        # The 'comment' field is required by the Serializer class definition (comment = CharField(..., required=True))
        # So we must provide it or it will fail earlier.
        # However, looking at the code snippet provided:
        # class ObservationLogApprovalSerializer(Serializer):
        #     ...
        #     comment = CharField(max_length=4096, required=True)
        # So 'comment' is mandatory.

        try:
            if not serializer.is_valid():
                self.fail(f"Validation failed unexpectedly: {serializer.errors}")
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError: {e}")

    def test_valid_approval_with_remark_raises_error(self):
        """Test that providing a rejection remark with an approval raises a validation error"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            rejection_remark="This should fail",  # Non-empty string
        )
        serializer = ObservationLogApprovalSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)

        # Check that the error message matches the expected logic
        # Note: DRF validation errors are often raised during is_valid() or explicit raise
        self.assertIn("Remark for rejection cannot be set with approval", str(context.exception))

    def test_valid_rejection_with_remark(self):
        """Test that valid rejection with a remark passes validation"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REJECTED,
            rejection_remark="This is invalid",  # Non-empty string required for rejection
            observation_log_comment="",
        )
        serializer = ObservationLogApprovalSerializer(data=data)

        # 'comment' is required by the class definition
        data["comment"] = "Valid comment for rejection"
        serializer = ObservationLogApprovalSerializer(data=data)

        try:
            if not serializer.is_valid():
                self.fail(f"Validation failed unexpectedly: {serializer.errors}")
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError: {e}")

    def test_invalid_rejection_without_remark(self):
        """Test that rejection without a remark raises a validation error"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REJECTED,
            rejection_remark="",  # Empty string is not allowed for rejection
        )
        # 'comment' is required by the class definition
        data["comment"] = "Valid comment"

        serializer = ObservationLogApprovalSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)

        self.assertIn("Rejection needs a remark", str(context.exception))

    def test_invalid_approval_with_observation_log_comment(self):
        """Test that providing an observation log comment with standard approval raises error"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            observation_log_comment="Some edit comment",  # Should not be allowed for standard approval
        )
        serializer = ObservationLogApprovalSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)

        self.assertIn("Comment for observation Log cannot be set with approval", str(context.exception))

    def test_invalid_rejection_with_observation_log_comment(self):
        """Test that providing an observation log comment with rejection raises error"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_REJECTED,
            rejection_remark="Rejected",
            observation_log_comment="Some edit comment",  # Should not be allowed for rejection
        )
        serializer = ObservationLogApprovalSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)

        self.assertIn("Comment for observation Log cannot be set with approval", str(context.exception))

    def test_valid_approval_with_edits_has_comment(self):
        """Test that APPROVED_WITH_EDITS works when comment is present"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
            observation_log_comment="Edits were made",
        )
        serializer = ObservationLogApprovalSerializer(data=data)

        try:
            if not serializer.is_valid():
                self.fail(f"Validation failed unexpectedly: {serializer.errors}")
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError: {e}")

    def test_invalid_approval_with_edits_no_comment(self):
        """Test that APPROVED_WITH_EDITS fails when comment is missing"""
        data = self._get_serializer_data(
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
            observation_log_comment="",  # Empty string as per default or omitted
        )
        serializer = ObservationLogApprovalSerializer(data=data)

        with self.assertRaises(ValidationError) as context:
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)

        self.assertIn("Approval with edits needs an observation log comment", str(context.exception))


class TestObservationLogBulkApprovalSerializer(BaseTestCase):
    """Tests for the validate method of ObservationLogBulkApprovalSerializer"""

    def test_approved_with_rejection_remark_raises(self):
        serializer = ObservationLogBulkApprovalSerializer()
        attrs = {
            "assessment_status": Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            "rejection_remark": "This should fail",
        }

        with self.assertRaises(ValidationError) as e:
            serializer.validate(attrs)

        self.assertIn("Remark for rejection cannot be set with approval", str(e.exception))

    def test_approved_without_rejection_remark_valid(self):
        serializer = ObservationLogBulkApprovalSerializer()
        attrs = {
            "assessment_status": Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            "rejection_remark": "",
        }

        new_attrs = serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)

    def test_rejected_without_rejection_remark_raises(self):
        serializer = ObservationLogBulkApprovalSerializer()
        attrs = {
            "assessment_status": Assessment_Status.ASSESSMENT_STATUS_REJECTED,
            "rejection_remark": "",
        }

        with self.assertRaises(ValidationError) as e:
            serializer.validate(attrs)

        self.assertIn("Rejection needs a remark", str(e.exception))

    def test_rejected_with_rejection_remark_valid(self):
        serializer = ObservationLogBulkApprovalSerializer()
        attrs = {
            "assessment_status": Assessment_Status.ASSESSMENT_STATUS_REJECTED,
            "rejection_remark": "This is invalid",
        }

        new_attrs = serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)

    def test_no_status_valid(self):
        serializer = ObservationLogBulkApprovalSerializer()
        attrs = {
            "rejection_remark": "",
        }

        new_attrs = serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)
