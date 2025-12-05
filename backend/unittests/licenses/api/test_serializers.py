from unittest.mock import patch

from rest_framework.serializers import ValidationError

from application.licenses.api.serializers import (
    LicenseGroupMemberSerializer,
    LicensePolicyItemSerializer,
    LicensePolicyMemberSerializer,
)
from application.licenses.models import (
    License,
    License_Group,
    License_Group_Member,
    License_Policy,
    License_Policy_Member,
)
from unittests.base_test_case import BaseTestCase


class TestLicenseGroupMemberSerializer(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.license_group_1 = License_Group.objects.get(id=1)
        self.license_group_member_1 = License_Group_Member(license_group=self.license_group_1, user=self.user_internal)
        self.license_group_member_serializer_1 = LicenseGroupMemberSerializer(self.license_group_member_1)

    def test_validate_license_group_change(self):
        license_group_2 = License_Group.objects.get(id=2)
        attrs = {"license_group": license_group_2}

        with self.assertRaises(ValidationError) as e:
            self.license_group_member_serializer_1.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='License group and user cannot be changed', code='invalid')]", str(e.exception)
        )

    def test_validate_user_change(self):
        attrs = {"user": self.user_external}

        with self.assertRaises(ValidationError) as e:
            self.license_group_member_serializer_1.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='License group and user cannot be changed', code='invalid')]", str(e.exception)
        )

    @patch("application.licenses.api.serializers.get_license_group_member")
    def test_validate_already_exists(self, mock_license_group_member):
        self.license_group_member_serializer_1.instance = None
        mock_license_group_member.return_value = self.license_group_member_1

        attrs = {"license_group": self.license_group_1, "user": self.user_internal}

        with self.assertRaises(ValidationError) as e:
            self.license_group_member_serializer_1.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='License group member Permissive Model (Blue Oak Council) / user_internal@example.com already exists', code='invalid')]",
            str(e.exception),
        )
        mock_license_group_member.assert_called_with(self.license_group_1, self.user_internal)


class TestLicensePolicyMemberSerializer(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.license_policy_1 = License_Policy.objects.get(id=1)
        self.license_policy_member_1 = License_Policy_Member(
            license_policy=self.license_policy_1, user=self.user_internal
        )
        self.license_policy_member_serializer_1 = LicensePolicyMemberSerializer(self.license_policy_member_1)

    def test_validate_license_policy_change(self):
        license_policy_2 = License_Policy(name="license_policy_2")
        attrs = {"license_policy": license_policy_2}

        with self.assertRaises(ValidationError) as e:
            self.license_policy_member_serializer_1.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='License policy and user cannot be changed', code='invalid')]", str(e.exception)
        )

    def test_validate_user_change(self):
        attrs = {"user": self.user_external}

        with self.assertRaises(ValidationError) as e:
            self.license_policy_member_serializer_1.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='License policy and user cannot be changed', code='invalid')]", str(e.exception)
        )

    @patch("application.licenses.api.serializers.get_license_policy_member")
    def test_validate_already_exists(self, mock_license_policy_member):
        self.license_policy_member_serializer_1.instance = None
        mock_license_policy_member.return_value = self.license_policy_member_1

        attrs = {"license_policy": self.license_policy_1, "user": self.user_internal}

        with self.assertRaises(ValidationError) as e:
            self.license_policy_member_serializer_1.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='License policy member Standard / user_internal@example.com already exists', code='invalid')]",
            str(e.exception),
        )
        mock_license_policy_member.assert_called_with(self.license_policy_1, self.user_internal)


class TestLicensePolicyItemSerializer(BaseTestCase):
    def test_one_must_be_set(self):
        license_policy_item_serializer = LicensePolicyItemSerializer()
        attrs = {}

        with self.assertRaises(ValidationError) as e:
            license_policy_item_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='One of license group, license, license expression or unknown license must be set', code='invalid')]",
            str(e.exception),
        )

    def test_only_one_must_be_set(self):
        license_policy_item_serializer = LicensePolicyItemSerializer()
        attrs = {
            "license_group": License_Group.objects.get(id=1),
            "license": License.objects.get(id=1),
            "license_expression": "license_expression",
            "non_spdx_license": "non_spdx_license",
        }

        with self.assertRaises(ValidationError) as e:
            license_policy_item_serializer.validate(attrs)

        self.assertEqual(
            "[ErrorDetail(string='Only one of license group, license, license expression or unknown license must be set', code='invalid')]",
            str(e.exception),
        )
