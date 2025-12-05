# backend/unittests/licenses/services/test_license_policy.py
from django.test import TestCase

from application.licenses.models import License_Group, License_Policy, License_Policy_Item
from application.licenses.services.license_policy import create_scancode_standard_policy
from application.licenses.types import License_Policy_Evaluation_Result


class TestCreateScancodeStandardPolicy(TestCase):
    def setUp(self):
        # Clear any existing license policies
        License_Policy.objects.exclude(parent__isnull=True).delete()
        License_Policy.objects.all().delete()
        License_Group.objects.all().delete()

    def test_create_scancode_standard_policy_creates_policy_when_none_exists(self):
        # Arrange
        # Ensure no "Standard" policy exists
        License_Policy.objects.filter(name="Standard").delete()

        # Create some license groups with ScanCode LicenseDB in their name
        License_Group.objects.create(name="Permissive (ScanCode LicenseDB)")
        License_Group.objects.create(name="Copyleft (ScanCode LicenseDB)")
        License_Group.objects.create(name="Public Domain (ScanCode LicenseDB)")
        License_Group.objects.create(name="Other Group (ScanCode LicenseDB)")
        License_Group.objects.create(name="Regular Group")

        # Act
        create_scancode_standard_policy()

        # Assert
        policy = License_Policy.objects.get(name="Standard")
        self.assertIsNotNone(policy)
        self.assertTrue(policy.is_public)
        self.assertEqual(policy.description, "Created automatically during initial startup")

        # Check that policy items were created for the ScanCode groups
        items = License_Policy_Item.objects.filter(license_policy=policy)
        self.assertEqual(items.count(), 4)  # Should have items for 4 groups with ScanCode LicenseDB

        # Check evaluation results based on group names
        for item in items:
            if item.license_group.name.startswith("Permissive") or item.license_group.name.startswith("Public Domain"):
                self.assertEqual(item.evaluation_result, License_Policy_Evaluation_Result.RESULT_ALLOWED)
            elif item.license_group.name.startswith("Copyleft"):
                self.assertEqual(item.evaluation_result, License_Policy_Evaluation_Result.RESULT_FORBIDDEN)
            else:
                # Other groups should default to REVIEW_REQUIRED
                self.assertEqual(item.evaluation_result, License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)

    def test_create_scancode_standard_policy_no_groups(self):
        # Arrange
        # Ensure no "Standard" policy exists
        License_Policy.objects.filter(name="Standard").delete()

        # Create a regular group without ScanCode LicenseDB
        License_Group.objects.create(name="Regular Group")

        # Act
        create_scancode_standard_policy()

        # Assert
        policy = License_Policy.objects.filter(name="Standard").first()
        self.assertIsNone(policy)  # Should not create policy when no ScanCode groups exist

    def test_create_scancode_standard_policy_already_exists(self):
        # Arrange
        # Create a "Standard" policy already
        policy = License_Policy.objects.create(
            name="Standard", description="Created automatically during initial startup", is_public=True
        )

        # Create some license groups
        group1 = License_Group.objects.create(name="Permissive (ScanCode LicenseDB)")
        group2 = License_Group.objects.create(name="Copyleft (ScanCode LicenseDB)")

        # Act
        create_scancode_standard_policy()

        # Assert
        # Should not create a new policy
        policies = License_Policy.objects.filter(name="Standard")
        self.assertEqual(policies.count(), 1)

        # Should not create new items
        items = License_Policy_Item.objects.filter(license_policy=policy)
        self.assertEqual(items.count(), 0)  # No new items should be created

    def test_create_scancode_standard_policy_no_scan_code_groups(self):
        # Arrange
        # Ensure no "Standard" policy exists
        License_Policy.objects.filter(name="Standard").delete()

        # Create groups without ScanCode LicenseDB
        License_Group.objects.create(name="Regular Group 1")
        License_Group.objects.create(name="Another Group")

        # Act
        create_scancode_standard_policy()

        # Assert
        policy = License_Policy.objects.filter(name="Standard").first()
        self.assertIsNone(policy)  # Should not create policy when no ScanCode groups exist
