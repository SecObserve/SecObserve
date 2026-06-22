from unittest.mock import patch

from django.core.management import call_command
from rest_framework.exceptions import PermissionDenied

from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from application.authorization.services.authorization import (
    NoAuthorizationImplementedError,
    PermissionDoesNotExistError,
    RoleDoesNotExistError,
    get_highest_user_role,
    role_has_permission,
    user_has_permission,
    user_has_permission_or_403,
)
from application.authorization.services.roles_permissions import Permissions, Roles
from application.core.models import (
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from unittests.base_test_case import BaseTestCase


class TestAuthorization(BaseTestCase):
    # ---------------------------------------------------------------
    # user_has_permission
    # ---------------------------------------------------------------

    @patch("application.authorization.services.authorization.get_current_user")
    def test_user_has_permission_superuser(self, mock):
        mock.return_value = self.user_admin
        self.assertTrue(user_has_permission(None, Permissions.Observation_Delete))

    # --- Product ---

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_product_no_permissions(self, mock):
        mock.return_value = None
        self.assertFalse(user_has_permission(self.product_1, Permissions.Product_Edit, self.user_internal))
        mock.assert_called_with(self.product_1, self.user_internal)

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_product_successful(self, mock):
        mock.return_value = Roles.Maintainer
        self.assertTrue(
            user_has_permission(
                self.product_1,
                Permissions.Product_Import_Observations,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Observation_Log_Approval grant for designated approvers ---

    @patch("application.authorization.services.authorization.is_user_designated_assessment_approver")
    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_approval_granted_to_approver_without_role_permission(self, mock_role, mock_approver):
        # Reader's role does not include Observation_Log_Approval, but a designated approver is granted it.
        mock_role.return_value = Roles.Reader
        mock_approver.return_value = True
        self.assertTrue(user_has_permission(self.product_1, Permissions.Observation_Log_Approval, self.user_internal))
        mock_approver.assert_called_with(self.product_1, self.user_internal)

    @patch("application.authorization.services.authorization.is_user_designated_assessment_approver")
    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_approval_granted_to_approver_without_role(self, mock_role, mock_approver):
        mock_role.return_value = None
        mock_approver.return_value = True
        self.assertTrue(user_has_permission(self.product_1, Permissions.Observation_Log_Approval, self.user_internal))
        mock_approver.assert_called_with(self.product_1, self.user_internal)

    @patch("application.authorization.services.authorization.is_user_designated_assessment_approver")
    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_approval_denied_to_non_approver(self, mock_role, mock_approver):
        mock_role.return_value = Roles.Reader
        mock_approver.return_value = False
        self.assertFalse(user_has_permission(self.product_1, Permissions.Observation_Log_Approval, self.user_internal))

    @patch("application.authorization.services.authorization.is_user_designated_assessment_approver")
    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_approval_role_grant_short_circuits(self, mock_role, mock_approver):
        # Writer already has Observation_Log_Approval by role, so the approver check is not needed.
        mock_role.return_value = Roles.Writer
        self.assertTrue(user_has_permission(self.product_1, Permissions.Observation_Log_Approval, self.user_internal))
        mock_approver.assert_not_called()

    @patch("application.authorization.services.authorization.is_user_designated_assessment_approver")
    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_approver_does_not_grant_other_permissions(self, mock_role, mock_approver):
        # Being a designated approver only grants approval, not assessment.
        mock_role.return_value = Roles.Reader
        mock_approver.return_value = True
        self.assertFalse(user_has_permission(self.product_1, Permissions.Observation_Assessment, self.user_internal))
        mock_approver.assert_not_called()

    # --- Product_Group ---

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_product_group_no_permissions(self, mock):
        mock.return_value = None
        self.assertFalse(user_has_permission(self.product_group_1, Permissions.Product_Edit, self.user_internal))
        mock.assert_called_with(self.product_group_1, self.user_internal)

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_product_group_successful(self, mock):
        mock.return_value = Roles.Maintainer
        self.assertTrue(
            user_has_permission(
                self.product_group_1,
                Permissions.Product_Import_Observations,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_group_1, self.user_internal)

    # --- Product_Member ---

    def test_user_has_permission_product_member_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.product_member_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Product_Member and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_product_member_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(
            user_has_permission(
                self.product_member_1,
                Permissions.Product_Member_Edit,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Product_Authorization_Group_Member ---

    def test_user_has_permission_product_authorization_group_member_wrong_permission(
        self,
    ):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(
                self.product_authorization_group_member_1,
                Permissions.Product_Edit,
                self.user_internal,
            )
        self.assertEqual(
            "No authorization implemented for class Product_Authorization_Group_Member and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_product_authorization_group_member_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(
            user_has_permission(
                self.product_authorization_group_member_1,
                Permissions.Product_Authorization_Group_Member_Edit,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Rule ---

    def test_user_has_permission_rule_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.product_rule_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Rule and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_rule_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(user_has_permission(self.product_rule_1, Permissions.Product_Rule_Edit, self.user_internal))
        mock.assert_called_with(self.product_1, self.user_internal)

    def test_user_has_permission_rule_general_rule(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.general_rule, Permissions.Product_Rule_View, self.user_internal)
        self.assertEqual("No authorization implemented for General Rules", str(e.exception))

    # --- Branch ---

    def test_user_has_permission_branch_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.branch_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Branch and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_branch_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(user_has_permission(self.branch_1, Permissions.Branch_Edit, self.user_internal))
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Service ---

    def test_user_has_permission_service_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.service_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Service and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_service_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(user_has_permission(self.service_1, Permissions.Service_Delete, self.user_internal))
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Observation ---

    def test_user_has_permission_observation_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.observation_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Observation and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_observation_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(user_has_permission(self.observation_1, Permissions.Observation_Delete, self.user_internal))
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Observation Log ---

    def test_user_has_permission_observation_log_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.observation_log_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Observation_Log and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_observation_log_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(
            user_has_permission(
                self.observation_log_1,
                Permissions.Observation_Log_Approval,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- Api_Configuration ---

    def test_user_has_permission_api_configuration_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.api_configuration_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Api_Configuration and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_api_configuration_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(
            user_has_permission(
                self.api_configuration_1,
                Permissions.Api_Configuration_Edit,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    # --- VEX_Base ---

    def test_user_has_permission_vex_base_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.openvex_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class OpenVEX and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_vex_base_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(
            user_has_permission(
                self.openvex_1,
                Permissions.VEX_Edit,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_vex_base_correct_user(self, mock):
        self.assertTrue(
            user_has_permission(
                self.openvex_1,
                Permissions.VEX_Edit,
                self.user_external,
            )
        )
        mock.assert_not_called()

    # --- Vulnerability_Check ---

    def test_user_has_permission_vulnerability_check_wrong_permission(self):
        with self.assertRaises(NoAuthorizationImplementedError) as e:
            user_has_permission(self.vulnerability_check_1, Permissions.Product_Edit, self.user_internal)
        self.assertEqual(
            "No authorization implemented for class Vulnerability_Check and permission 1102",
            str(e.exception),
        )

    @patch("application.authorization.services.authorization.get_highest_user_role")
    def test_user_has_permission_vulnerability_check_correct_permission(self, mock):
        mock.return_value = None
        self.assertFalse(
            user_has_permission(
                self.vulnerability_check_1,
                Permissions.Product_View,
                self.user_internal,
            )
        )
        mock.assert_called_with(self.product_1, self.user_internal)

    # ---------------------------------------------------------------
    # user_has_permission_or_403
    # ---------------------------------------------------------------

    @patch("application.authorization.services.authorization.user_has_permission")
    def test_user_has_permission_or_403_permission_denied(self, mock):
        mock.return_value = False
        with self.assertRaises(PermissionDenied):
            user_has_permission_or_403(None, Permissions.Product_Edit)

    @patch("application.authorization.services.authorization.user_has_permission")
    def test_user_has_permission_or_403_successful(self, mock):
        mock.return_value = True
        user_has_permission_or_403(None, Permissions.Product_Edit)

    # ---------------------------------------------------------------
    # role_has_permission
    # ---------------------------------------------------------------

    def test_role_has_permission_wrong_role(self):
        with self.assertRaises(RoleDoesNotExistError) as e:
            role_has_permission(99999, Permissions.Product_Edit)
        self.assertEqual("Role 99999 does not exist", str(e.exception))

    def test_role_has_permission_wrong_permission(self):
        with self.assertRaises(PermissionDoesNotExistError) as e:
            role_has_permission(Roles.Reader, 99999)
        self.assertEqual("Permission 99999 does not exist", str(e.exception))

    @patch("application.authorization.services.authorization.get_roles_with_permissions")
    def test_role_has_permission_no_permission(self, mock):
        mock.return_value = {Roles.Reader: {}}
        self.assertFalse(role_has_permission(Roles.Reader, Permissions.Observation_Delete))

    def test_role_has_permission_not_permitted(self):
        self.assertFalse(role_has_permission(Roles.Maintainer, Permissions.Observation_Delete))

    def test_role_has_permission_successful(self):
        self.assertTrue(role_has_permission(Roles.Owner, Permissions.Observation_Delete))

    # ---------------------------------------------------------------
    # get_highest_user_role
    # ---------------------------------------------------------------

    def test_get_highest_user_role_product_member(self):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        self._test_get_highest_user_role()

    def test_get_highest_user_role_product_authorization_group_member(self):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        prepare_authorization_groups()
        self._test_get_highest_user_role()

    def _test_get_highest_user_role(self):
        product = Product.objects.get(name="db_product_internal")

        user = User.objects.get(username="db_admin")
        role = get_highest_user_role(product, user)
        self.assertEqual(Roles.Owner, role)

        user = User.objects.get(username="db_internal_write")
        role = get_highest_user_role(product, user)
        self.assertEqual(Roles.Owner, role)

        user = User.objects.get(username="db_internal_read")
        role = get_highest_user_role(product, user)
        self.assertEqual(Roles.Reader, role)

        user = User.objects.get(username="db_external")
        role = get_highest_user_role(product, user)
        self.assertIsNone(role)

        user = User.objects.get(username="db_product_group_user")
        role = get_highest_user_role(product, user)
        self.assertEqual(Roles.Owner, role)


# ---------------------------------------------------------------
# helper functions
# ---------------------------------------------------------------


def prepare_authorization_groups():
    call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

    Product_Member.objects.all().delete()
    Authorization_Group.objects.all().delete()
    Product_Authorization_Group_Member.objects.all().delete()

    product_internal = Product.objects.get(name="db_product_internal")
    product_external = Product.objects.get(name="db_product_external")
    product_group = Product.objects.get(name="db_product_group")

    user_internal_write = User.objects.get(username="db_internal_write")
    group_internal_write = Authorization_Group.objects.create(name="db_group_internal_write")
    Authorization_Group_Member.objects.filter(authorization_group=group_internal_write).delete()
    Authorization_Group_Member.objects.create(
        authorization_group=group_internal_write,
        user=user_internal_write,
        is_manager=True,
    )
    Product_Authorization_Group_Member.objects.create(
        product=product_internal, authorization_group=group_internal_write, role=5
    )

    group_internal_read = Authorization_Group.objects.create(name="db_group_internal_read")
    Authorization_Group_Member.objects.filter(authorization_group=group_internal_read).delete()
    Authorization_Group_Member.objects.create(
        authorization_group=group_internal_read,
        user=User.objects.get(id=3),
        is_manager=False,
    )
    Product_Authorization_Group_Member.objects.create(
        product=product_internal, authorization_group=group_internal_read, role=1
    )

    group_external = Authorization_Group.objects.create(name="db_group_external")
    Authorization_Group_Member.objects.filter(authorization_group=group_external).delete()
    Authorization_Group_Member.objects.create(
        authorization_group=group_external,
        user=User.objects.get(id=4),
        is_manager=False,
    )
    Product_Authorization_Group_Member.objects.create(
        product=product_external, authorization_group=group_external, role=5
    )

    group_product_group = Authorization_Group.objects.create(name="db_group_product_group")
    Authorization_Group_Member.objects.filter(authorization_group=group_product_group).delete()
    Authorization_Group_Member.objects.create(
        authorization_group=group_product_group,
        user=User.objects.get(id=6),
        is_manager=False,
    )
    Product_Authorization_Group_Member.objects.create(
        product=product_group, authorization_group=group_product_group, role=5
    )

    group_unused = Authorization_Group.objects.create(name="db_group_unused")
    Authorization_Group_Member.objects.filter(authorization_group=group_unused).delete()
