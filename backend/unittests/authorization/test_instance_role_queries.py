from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import Authorization_Group, User
from application.authorization.services.authorization import (
    get_highest_user_role,
    user_has_permission,
)
from application.authorization.services.roles_permissions import Permissions, Roles
from application.core.models import (
    Component,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.core.queries.branch import get_branches
from application.core.queries.component import get_components
from application.core.queries.observation import (
    get_evidences,
    get_observation_logs,
    get_observations,
    get_potential_duplicates,
)
from application.core.queries.product import get_products
from application.core.queries.product_member import (
    get_product_authorization_group_members,
    get_product_members,
)
from application.core.queries.service import get_services
from application.import_observations.queries.api_configuration import (
    get_api_configurations,
)
from application.import_observations.queries.vulnerability_check import (
    get_vulnerability_checks,
)
from application.licenses.queries.concluded_license import get_concluded_licenses
from application.licenses.queries.license_component import get_license_components
from application.licenses.queries.license_component_evidence import (
    get_license_component_evidences,
)
from application.metrics.queries.product_metrics import get_product_metrics
from application.notifications.models import Notification
from application.notifications.queries.notification import get_notifications
from application.rules.queries.rule import get_product_rules
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.queries.scancodeio_project import get_scancodeio_projects
from application.vex.models import CSAF, CycloneDX, OpenVEX
from application.vex.queries.csaf import get_csafs
from application.vex.queries.cyclonedx import get_cyclonedx_s
from application.vex.queries.openvex import get_openvex_s
from unittests.base_test_case import BaseTestCase

CURRENT_USER = "application.access_control.services.current_user.get_current_request"

LIST_FUNCTIONS = [
    get_branches,
    get_observations,
    get_evidences,
    get_potential_duplicates,
    get_observation_logs,
    get_products,
    get_product_members,
    get_product_authorization_group_members,
    get_services,
    get_api_configurations,
    get_vulnerability_checks,
    get_concluded_licenses,
    get_license_components,
    get_license_component_evidences,
    get_product_metrics,
    get_product_rules,
    get_scancodeio_projects,
]


class TestInstanceRoleQueries(BaseTestCase):
    patch.TEST_PREFIX = (
        "test",
        "setUp",
    )

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.admin = User.objects.get(username="db_admin")
        self.service_account = User.objects.create(
            username="sa_instance_role", is_service_account=True, instance_role=Roles.Reader
        )
        # There are no fixtures for these models
        Product_Authorization_Group_Member.objects.create(
            product_id=1, authorization_group=Authorization_Group.objects.first(), role=Roles.Reader
        )
        ScanCodeIO_Project.objects.create(
            product_id=1,
            project_uuid="b7a3c1de-0000-4000-8000-000000000001",
            project_name="project",
            webhook_token_hash="hash",
        )

    def _as(self, user):
        return patch(CURRENT_USER, return_value=SimpleNamespace(user=user))

    def _pks(self, function):
        return sorted(function().values_list("pk", flat=True))

    def test_instance_role_sees_what_superuser_sees(self):
        for function in LIST_FUNCTIONS:
            with self.subTest(function=function.__name__):
                with self._as(self.admin):
                    expected = self._pks(function)
                self.assertTrue(expected, "There must be data to compare")
                with self._as(self.service_account):
                    self.assertEqual(expected, self._pks(function))

    def test_upload_instance_role_sees_nothing_but_can_import(self):
        self.service_account.instance_role = Roles.Upload
        self.service_account.save()
        product = Product.objects.get(pk=1)
        Notification.objects.create(type=Notification.TYPE_SECURITY_GATE, name="gate", message="m", product=product)
        functions = [*LIST_FUNCTIONS, get_components, get_notifications, get_csafs, get_cyclonedx_s, get_openvex_s]
        for function in functions:
            with self.subTest(function=function.__name__):
                with self._as(self.admin):
                    self.assertTrue(self._pks(function), "There must be data to hide")
                with self._as(self.service_account):
                    self.assertEqual([], self._pks(function))

        self.assertTrue(user_has_permission(product, Permissions.Product_Import_Observations, self.service_account))

    def test_upload_instance_role_sees_products_of_memberships(self):
        self.service_account.instance_role = Roles.Upload
        self.service_account.save()
        Product_Member.objects.create(product_id=1, user=self.service_account, role=Roles.Reader)
        with self._as(self.service_account):
            self.assertEqual([1], self._pks(get_products))

    def test_maintainer_instance_role_cannot_become_owner_with_product_group(self):
        self.service_account.instance_role = Roles.Maintainer
        self.service_account.save()
        client = APIClient()
        client.force_authenticate(user=self.service_account)

        response = client.post("/api/product_groups/", {"name": "own group"}, "json")
        self.assertEqual(201, response.status_code, response.content)
        response = client.patch("/api/products/2/", {"product_group": response.data["id"]}, "json")

        self.assertEqual(400, response.status_code)
        self.assertIn("You need to be an Owner of the product", response.content.decode())
        self.assertEqual(Roles.Maintainer, get_highest_user_role(Product.objects.get(pk=2), self.service_account))

    def test_service_account_without_instance_role_sees_nothing(self):
        self.service_account.instance_role = None
        self.service_account.save()
        with self._as(self.service_account):
            self.assertEqual(0, get_products().count())

    def test_instance_role_notifications_exclude_exceptions(self):
        product = Product.objects.first()
        exception = Notification.objects.create(type=Notification.TYPE_EXCEPTION, name="exception", message="m")
        task = Notification.objects.create(type=Notification.TYPE_TASK, name="task", message="m")
        gate = Notification.objects.create(
            type=Notification.TYPE_SECURITY_GATE, name="gate", message="m", product=product
        )
        with self._as(self.service_account):
            self.assertEqual([gate], list(get_notifications().filter(id__in=[exception.id, task.id, gate.id])))

    def test_instance_role_components_hide_orphans(self):
        orphan = Component.objects.get(pk=3)
        with_observations = Component.objects.get(pk=1)
        with self._as(self.admin):
            self.assertIn(orphan, get_components())
        with self._as(self.service_account):
            components = get_components()
            self.assertNotIn(orphan, components)
            self.assertIn(with_observations, components)

    def test_instance_role_vex_without_product(self):
        product = Product.objects.first()
        now = timezone.now()
        csaf_fields = {
            "title": "title",
            "tlp_label": "WHITE",
            "tracking_status": "draft",
            "publisher_name": "name",
            "publisher_category": "vendor",
            "publisher_namespace": "https://example.com",
        }
        cyclonedx_fields = {"first_issued": now, "last_updated": now}
        openvex_fields = {
            "id_namespace": "https://example.com",
            "author": "author",
            "timestamp": now,
            "last_updated": now,
        }
        for model, query, fields in [
            (CSAF, get_csafs, csaf_fields),
            (CycloneDX, get_cyclonedx_s, cyclonedx_fields),
            (OpenVEX, get_openvex_s, openvex_fields),
        ]:
            with self.subTest(model=model.__name__):
                documents = [
                    model.objects.create(
                        user=user,
                        product=document_product,
                        document_id_prefix=f"prefix{index}",
                        document_base_id=f"base{index}",
                        version=1,
                        **fields,
                    )
                    for index, (document_product, user) in enumerate(
                        [(product, self.admin), (None, self.admin), (None, self.service_account)]
                    )
                ]
                with self._as(self.service_account):
                    visible = list(query().filter(id__in=[d.id for d in documents]))
                self.assertEqual([documents[0], documents[2]], visible)
