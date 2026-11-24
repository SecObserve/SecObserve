from unittest.mock import patch

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import Product_Member
from application.core.services.assessment_approver import _get_highest_user_role
from unittests.base_test_case import BaseTestCase

MODULE = "application.core.services.assessment_approver"


class TestAssessmentApprover(BaseTestCase):
    @patch(f"{MODULE}.get_highest_role_of_product_authorization_group_members_for_user")
    @patch(f"{MODULE}.get_product_member")
    def test_get_highest_user_role_counts_instance_role(self, mock_member, mock_group_role):
        mock_group_role.return_value = 0
        user = User(id=2, username="sa", is_service_account=True, instance_role=Roles.Maintainer)

        mock_member.return_value = None
        self.assertEqual(Roles.Maintainer, _get_highest_user_role(self.product_1, user))

        mock_member.return_value = Product_Member(role=Roles.Owner)
        self.assertEqual(Roles.Owner, _get_highest_user_role(self.product_1, user))
