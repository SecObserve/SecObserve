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
