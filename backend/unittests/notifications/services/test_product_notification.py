from unittest.mock import patch

from django.core.management import call_command

from application.access_control.models import Authorization_Group, User
from application.core.models import Product, Product_Authorization_Group_Member
from application.notifications.models import Product_Notification
from application.notifications.services.product_notification import (
    create_product_notification_override,
    get_or_create_template,
    get_product_notification,
    get_template_notification,
    get_users_for_product_notification,
    is_product_api_token_user,
)
from application.notifications.types import Product_Notification_Type
from unittests.base_test_case import BaseTestCase


class TestProductNotificationService(BaseTestCase):
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

    def setUp(self) -> None:
        super().setUp()

        # get_product_notification() only returns rows the current user is allowed to see, which is
        # resolved in the notifications query and again in get_products() of the core queries
        self._current_user = None
        for target in (
            "application.notifications.queries.product_notification.get_current_user",
            "application.core.queries.product.get_current_user",
        ):
            patcher = patch(target, side_effect=lambda: self._current_user)
            patcher.start()
            self.addCleanup(patcher.stop)

        # get_users_for_product_notification() only returns users who can be reached by email,
        # the users of the fixtures have none
        for user in User.objects.all():
            user.email = f"{user.username}@example.com"
            user.save()

    def _set_current_user(self, username: str) -> User:
        self._current_user = User.objects.get(username=username)
        return self._current_user

    # --- is_product_api_token_user ---

    def test_is_product_api_token_user(self):
        self.assertTrue(is_product_api_token_user(User.objects.get(username="-product-2-api_token-")))
        self.assertFalse(is_product_api_token_user(User.objects.get(username="db_internal_write")))

    # --- get_or_create_template ---

    def test_get_or_create_template_creates_once(self):
        user = User.objects.get(username="db_internal_write")

        template = get_or_create_template(user)

        self.assertIsNone(template.product)
        self.assertEqual(user, template.user)
        self.assertEqual(template, get_or_create_template(user))
        self.assertEqual(1, Product_Notification.objects.filter(user=user, product__isnull=True).count())

    def test_get_or_create_template_tolerates_duplicates(self):
        # The unique constraint cannot cover the template, because NULLs are distinct in a unique index
        user = User.objects.get(username="db_internal_write")
        first = Product_Notification.objects.create(user=user)
        Product_Notification.objects.create(user=user)

        self.assertEqual(first, get_or_create_template(user))

    # --- get_product_notification ---

    def test_get_product_notification_without_override(self):
        user = self._set_current_user("db_internal_write")

        self.assertIsNone(get_product_notification(Product.objects.get(pk=1), user))

    def test_get_product_notification_with_override(self):
        user = self._set_current_user("db_internal_write")
        existing = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1))

        self.assertEqual(existing, get_product_notification(Product.objects.get(pk=1), user))

    # --- get_template_notification ---

    def test_get_template_notification_is_the_product_group(self):
        # db_product_group_user is a member of product group 3, the product group of product 1
        user = self._set_current_user("db_product_group_user")
        create_product_notification_override(Product.objects.get(pk=3), user)

        parent = get_template_notification(Product.objects.get(pk=1), user)

        self.assertEqual(3, parent.product_id)

    def test_get_template_notification_ignores_an_invisible_product_group(self):
        # db_internal_write is a member of product 1, but not of its product group 3, so their
        # settings for the product group are not inherited
        user = self._set_current_user("db_internal_write")
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3))

        parent = get_template_notification(Product.objects.get(pk=1), user)

        self.assertIsNone(parent.product)

    def test_get_template_notification_is_the_template_without_product_group_override(self):
        # product 1 belongs to product group 3, but the user does not override the product group
        user = self._set_current_user("db_internal_write")

        parent = get_template_notification(Product.objects.get(pk=1), user)

        self.assertIsNone(parent.product)
        # the settings of the product group must not be created as a side effect
        self.assertFalse(Product_Notification.objects.filter(user=user, product=3).exists())

    def test_get_template_notification_without_product_group(self):
        # product 2 does not belong to a product group
        user = self._set_current_user("db_internal_read")

        parent = get_template_notification(Product.objects.get(pk=2), user)

        self.assertIsNone(parent.product)

    def test_get_template_notification_of_a_product_group_is_the_template(self):
        user = self._set_current_user("db_product_group_user")

        parent = get_template_notification(Product.objects.get(pk=3), user)

        self.assertIsNone(parent.product)

    # --- create_product_notification_override ---

    def test_create_product_notification_override_copies_the_template_values(self):
        # product 2 does not belong to a product group, so it inherits from the template
        user = self._set_current_user("db_internal_read")
        template = get_or_create_template(user)
        template.security_gate_changed = True
        template.observation_new_changed = True
        template.save()

        product_notification = create_product_notification_override(Product.objects.get(pk=2), user)

        self.assertTrue(product_notification.security_gate_changed)
        self.assertTrue(product_notification.observation_new_changed)
        self.assertFalse(product_notification.observation_to_be_reviewed)
        self.assertFalse(product_notification.assessment_to_be_reviewed)
        self.assertFalse(product_notification.product_rule_to_be_reviewed)

    def test_create_product_notification_override_copies_the_product_group_values(self):
        # product group 3 is the product group of product 1
        user = self._set_current_user("db_product_group_user")
        template = get_or_create_template(user)
        template.security_gate_changed = True
        template.save()
        product_group_notification = create_product_notification_override(Product.objects.get(pk=3), user)
        product_group_notification.security_gate_changed = False
        product_group_notification.observation_to_be_reviewed = True
        product_group_notification.save()

        product_notification = create_product_notification_override(Product.objects.get(pk=1), user)

        # the settings of the product group win over the template, in both directions
        self.assertFalse(product_notification.security_gate_changed)
        self.assertTrue(product_notification.observation_to_be_reviewed)

    def test_create_product_notification_override_without_product_group_override(self):
        # product 1 belongs to product group 3, but the user does not override the product group
        user = self._set_current_user("db_internal_write")
        template = get_or_create_template(user)
        template.product_rule_to_be_reviewed = True
        template.save()

        product_notification = create_product_notification_override(Product.objects.get(pk=1), user)

        self.assertTrue(product_notification.product_rule_to_be_reviewed)
        # only the template and the settings of the product are needed
        self.assertFalse(Product_Notification.objects.filter(user=user, product=3).exists())
        self.assertEqual(2, Product_Notification.objects.filter(user=user).count())

    def test_create_product_notification_override_for_a_product_group(self):
        user = self._set_current_user("db_product_group_user")
        template = get_or_create_template(user)
        template.observation_new_changed = True
        template.save()

        product_group_notification = create_product_notification_override(Product.objects.get(pk=3), user)

        self.assertEqual(3, product_group_notification.product_id)
        self.assertTrue(product_group_notification.observation_new_changed)

    def test_create_product_notification_override_returns_the_existing_row(self):
        user = self._set_current_user("db_internal_write")
        existing = Product_Notification.objects.create(
            user=user, product=Product.objects.get(pk=1), security_gate_changed=True
        )

        product_notification = create_product_notification_override(Product.objects.get(pk=1), user)

        self.assertEqual(existing, product_notification)
        self.assertTrue(product_notification.security_gate_changed)
        # no template is needed when the row already exists
        self.assertFalse(Product_Notification.objects.filter(user=user, product__isnull=True).exists())

    def test_create_product_notification_override_is_idempotent(self):
        user = self._set_current_user("db_internal_write")
        product = Product.objects.get(pk=1)

        first = create_product_notification_override(product, user)
        first.observation_new_changed = True
        first.save()
        second = create_product_notification_override(product, user)

        self.assertEqual(first, second)
        # the existing settings are returned unchanged
        self.assertTrue(second.observation_new_changed)
        self.assertEqual(1, Product_Notification.objects.filter(user=user, product=1).count())

    def test_create_product_notification_override_is_per_product(self):
        user = self._set_current_user("db_internal_read")

        first = create_product_notification_override(Product.objects.get(pk=1), user)
        second = create_product_notification_override(Product.objects.get(pk=2), user)

        self.assertNotEqual(first, second)
        self.assertEqual(2, Product_Notification.objects.filter(user=user, product__isnull=False).count())

    # --- get_users_for_product_notification ---

    def _get_usernames_for_product_notification(self, product_id: int) -> set[str]:
        users = get_users_for_product_notification(
            Product.objects.get(pk=product_id),
            Product_Notification_Type.SECURITY_GATE_CHANGED,
        )
        return {user.username for user in users}

    def test_get_users_for_product_notification_with_unknown_type(self):
        with self.assertRaises(ValueError):
            get_users_for_product_notification(Product.objects.get(pk=1), "not_a_notification_type")

    def test_get_users_for_product_notification_without_settings(self):
        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_from_the_template(self):
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=True)

        self.assertEqual({"db_internal_write"}, self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_without_product_group(self):
        # product 2 does not belong to a product group, db_external is a member of it
        Product_Notification.objects.create(user=User.objects.get(username="db_external"), security_gate_changed=True)

        self.assertEqual({"db_external"}, self._get_usernames_for_product_notification(2))

    def test_get_users_for_product_notification_from_the_product_group(self):
        # product group 3 is the product group of product 1
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=False)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), security_gate_changed=True)

        self.assertEqual({"db_internal_write"}, self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_from_the_product(self):
        # the settings of the product win over the product group and the template
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=False)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), security_gate_changed=False)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1), security_gate_changed=True)

        self.assertEqual({"db_internal_write"}, self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_switched_off_by_the_product(self):
        # the settings of the product win in the other direction as well
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), security_gate_changed=True)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1), security_gate_changed=False)

        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_switched_off_by_the_product_group(self):
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), security_gate_changed=False)

        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_with_duplicate_templates(self):
        # The unique constraint cannot cover the template, the lowest id wins
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        Product_Notification.objects.create(user=user, security_gate_changed=False)

        self.assertEqual({"db_internal_write"}, self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_is_per_type(self):
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, observation_new_changed=True)

        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_of_a_non_member(self):
        # db_admin is a superuser, but a member of nothing
        Product_Notification.objects.create(user=User.objects.get(username="db_admin"), security_gate_changed=True)

        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_of_a_product_group_member(self):
        # db_product_group_user is a member of product group 3, which product 1 belongs to
        Product_Notification.objects.create(
            user=User.objects.get(username="db_product_group_user"), security_gate_changed=True
        )

        self.assertEqual({"db_product_group_user"}, self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_of_an_authorization_group_member(self):
        user = User.objects.get(username="db_external")
        authorization_group = Authorization_Group.objects.create(name="notification_group")
        authorization_group.users.add(user)
        Product_Authorization_Group_Member.objects.create(
            product=Product.objects.get(pk=1),
            authorization_group=authorization_group,
            role=1,
        )
        Product_Notification.objects.create(user=user, security_gate_changed=True)

        self.assertEqual({"db_external"}, self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_excludes_product_api_token_users(self):
        # the user of the API token of product 2 is a member of it
        Product_Notification.objects.create(
            user=User.objects.get(username="-product-2-api_token-"), security_gate_changed=True
        )

        self.assertEqual(set(), self._get_usernames_for_product_notification(2))

    def test_get_users_for_product_notification_excludes_users_without_email(self):
        user = User.objects.get(username="db_internal_write")
        user.email = ""
        user.save()
        Product_Notification.objects.create(user=user, security_gate_changed=True)

        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_excludes_inactive_users(self):
        user = User.objects.get(username="db_internal_write")
        user.is_active = False
        user.save()
        Product_Notification.objects.create(user=user, security_gate_changed=True)

        self.assertEqual(set(), self._get_usernames_for_product_notification(1))

    def test_get_users_for_product_notification_of_several_users(self):
        # db_internal_write and db_internal_read are members of product 1, db_external is not
        for username in ("db_internal_write", "db_internal_read", "db_external"):
            Product_Notification.objects.create(user=User.objects.get(username=username), security_gate_changed=True)

        self.assertEqual({"db_internal_write", "db_internal_read"}, self._get_usernames_for_product_notification(1))
