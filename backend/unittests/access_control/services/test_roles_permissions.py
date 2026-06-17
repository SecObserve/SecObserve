from application.authorization.services.roles_permissions import (
    Permissions,
    Roles,
    get_permissions_for_role,
)
from unittests.base_test_case import BaseTestCase


class TestRolesPermissions(BaseTestCase):
    def test_get_permissions_for_role_not_found(self):
        self.assertIsNone(get_permissions_for_role(99999))

    def test_get_permissions_for_role_successful(self):
        permissions = {
            Permissions.Product_Group_View,
            Permissions.Product_View,
            Permissions.Product_Member_View,
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Branch_View,
            Permissions.Product_Rule_View,
            Permissions.Observation_View,
            Permissions.Api_Configuration_View,
            Permissions.Service_View,
            Permissions.VEX_View,
            Permissions.Concluded_License_View,
        }
        self.assertEqual(permissions, get_permissions_for_role(Roles.Reader))

    def test_get_permissions_for_role_writer(self):
        permissions = {
            Permissions.Product_Group_View,
            Permissions.Product_View,
            Permissions.Product_Import_Observations,
            Permissions.Product_Scan_OSV,
            Permissions.Product_Member_View,
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Product_Rule_View,
            Permissions.Branch_View,
            Permissions.Service_View,
            Permissions.Observation_View,
            Permissions.Observation_Create,
            Permissions.Observation_Log_Approval,
            Permissions.Api_Configuration_View,
            Permissions.VEX_View,
            Permissions.License_Component_Edit,
            Permissions.Concluded_License_View,
            Permissions.Concluded_License_Edit,
            Permissions.Concluded_License_Create,
        }
        self.assertEqual(permissions, get_permissions_for_role(Roles.Writer))

    def test_get_permissions_for_role_writer_cannot_edit_or_assess_observations(self):
        writer_permissions = get_permissions_for_role(Roles.Writer)
        self.assertNotIn(Permissions.Observation_Edit, writer_permissions)
        self.assertNotIn(Permissions.Observation_Assessment, writer_permissions)
        self.assertIn(Permissions.Observation_View, writer_permissions)
        self.assertIn(Permissions.Observation_Create, writer_permissions)
