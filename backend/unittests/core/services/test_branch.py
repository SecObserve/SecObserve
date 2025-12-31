from unittest.mock import patch

from django.test import TestCase

from application.core.models import Branch, Product
from application.core.services.branch import set_default_branch


class TestSetBranchService(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Product", repository_default_branch=None)
        self.branch_non_default = Branch.objects.create(
            name="non_default", product=self.product, is_default_branch=False
        )
        self.branch_default = Branch.objects.create(name="default", product=self.product, is_default_branch=True)

    @patch("application.core.services.branch.Branch.objects")
    @patch("application.core.services.branch.Branch.save")
    @patch("application.core.models.Product.save")
    def test_set_default_branch_when_branch_is_already_default(
        self, mock_product_save, mock_branch_save, mock_branch_objects
    ):
        # Set up the branch as default
        self.branch_non_default.is_default_branch = True

        # Create another branch for the same product
        other_branch = Branch(name="develop", product=self.product, is_default_branch=True)

        # Mock the filter to return the other branch
        mock_branch_objects.filter.return_value.exclude.return_value = [other_branch]

        set_default_branch(self.branch_non_default, False)

        # Verify that the other branch was set to not default
        self.assertFalse(other_branch.is_default_branch)
        mock_branch_save.assert_called()

        # Verify that product's repository_default_branch was set
        self.assertEqual(self.product.repository_default_branch, self.branch_non_default)
        mock_product_save.assert_called()

        # Verify the filter has been called with the correct arguments
        mock_branch_objects.filter.assert_called_once_with(product=self.product, is_default_branch=True)
        mock_branch_objects.filter().exclude.assert_called_once_with(pk=self.branch_non_default.pk)

    @patch("application.core.services.branch.Branch.save")
    @patch("application.core.models.Product.save")
    def test_set_default_branch_when_branch_is_not_default_and_not_product_default(
        self, mock_product_save, mock_branch_save
    ):
        # Set up product with a default branch
        self.product.repository_default_branch = self.branch_default

        # Set up the branch as not default
        self.branch_default.is_default_branch = False

        set_default_branch(self.branch_default, False)

        # Verify that product's repository_default_branch was set to None
        self.assertIsNone(self.product.repository_default_branch)
        mock_branch_save.assert_not_called()
        mock_product_save.assert_called()

    @patch("application.core.services.branch.Branch.save")
    @patch("application.core.models.Product.save")
    def test_set_default_branch_when_branch_is_not_default_and_product_has_no_default(
        self, mock_product_save, mock_branch_save
    ):
        # Product has no default branch set
        self.product.repository_default_branch = None

        # Set up the branch as not default
        self.branch_default.is_default_branch = False

        set_default_branch(self.branch_default, False)

        # Verify that nothing changed
        self.assertIsNone(self.product.repository_default_branch)
        mock_branch_save.assert_not_called()
        mock_product_save.assert_not_called()

    @patch("application.core.services.branch.Branch.objects")
    @patch("application.core.services.branch.Branch.save")
    @patch("application.core.models.Product.save")
    def test_set_default_branch_with_multiple_other_default_branches(
        self, mock_product_save, mock_branch_save, mock_branch_objects
    ):
        # Set up the branch as default
        self.branch_non_default.is_default_branch = True

        # Create multiple other branches for the same product
        branch1 = Branch(name="branch1", product=self.product, is_default_branch=True)
        branch2 = Branch(name="branch2", product=self.product, is_default_branch=True)

        # Mock the filter to return the other branches
        mock_branch_objects.filter.return_value.exclude.return_value = [branch1, branch2]

        set_default_branch(self.branch_non_default, False)

        # Verify that all other branches were set to not default
        self.assertFalse(branch1.is_default_branch)
        self.assertFalse(branch2.is_default_branch)
        self.assertEqual(mock_branch_save.call_count, 2)  # 2 other branches

        # Verify that product's repository_default_branch was set
        self.assertEqual(self.product.repository_default_branch, self.branch_non_default)
        mock_product_save.assert_called()

        # Verify the filter has been called with the correct arguments
        mock_branch_objects.filter.assert_called_once_with(product=self.product, is_default_branch=True)
        mock_branch_objects.filter().exclude.assert_called_once_with(pk=self.branch_non_default.pk)

    @patch("application.core.services.branch.Branch.objects")
    @patch("application.core.services.branch.Branch.save")
    @patch("application.core.models.Product.save")
    def test_is_default_branch_not_dirty(self, mock_product_save, mock_branch_save, mock_branch_objects):
        set_default_branch(self.branch_non_default, False)

        # Verify no mocks have been called
        mock_branch_objects.filter.assert_not_called()
        mock_branch_objects.filter().exclude.assert_not_called()
        mock_product_save.assert_not_called()
        mock_branch_save.assert_not_called()
