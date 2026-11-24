from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import Product
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
from application.scancodeio.queries.scancodeio_project import get_scancodeio_projects
from application.vex.models import CSAF
from application.vex.queries.csaf import get_csafs
from unittests.base_test_case import BaseTestCase

CURRENT_USER = "application.access_control.services.current_user.get_current_request"

LIST_FUNCTIONS = [
    get_branches,
    get_components,
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
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.admin = User.objects.get(username="db_admin")
        self.service_account = User.objects.create(
            username="sa_instance_role", is_service_account=True, instance_role=Roles.Reader
        )

    def _as(self, user):
        return patch(CURRENT_USER, return_value=SimpleNamespace(user=user))

    def test_instance_role_sees_what_superuser_sees(self):
        for function in LIST_FUNCTIONS:
            with self.subTest(function=function.__name__):
                with self._as(self.admin):
                    expected = function().count()
                with self._as(self.service_account):
                    self.assertEqual(expected, function().count())

    def test_service_account_without_instance_role_sees_nothing(self):
        self.service_account.instance_role = None
        self.service_account.save()
        with self._as(self.service_account):
            self.assertEqual(0, get_products().count())

    def test_instance_role_notifications_exclude_exceptions(self):
        product = Product.objects.first()
        exception = Notification.objects.create(type=Notification.TYPE_EXCEPTION, name="exception", message="m")
        gate = Notification.objects.create(
            type=Notification.TYPE_SECURITY_GATE, name="gate", message="m", product=product
        )
        with self._as(self.service_account):
            self.assertEqual([gate], list(get_notifications().filter(id__in=[exception.id, gate.id])))

    def test_instance_role_vex_without_product(self):
        product = Product.objects.first()
        csafs = []
        for index, (csaf_product, user) in enumerate(
            [(product, self.admin), (None, self.admin), (None, self.service_account)]
        ):
            csafs.append(
                CSAF.objects.create(
                    user=user,
                    product=csaf_product,
                    document_id_prefix=f"prefix{index}",
                    document_base_id=f"base{index}",
                    version=1,
                    title="title",
                    tlp_label="WHITE",
                    tracking_status="draft",
                    publisher_name="name",
                    publisher_category="vendor",
                    publisher_namespace="https://example.com",
                )
            )
        with self._as(self.service_account):
            self.assertEqual([csafs[0], csafs[2]], list(get_csafs().filter(id__in=[c.id for c in csafs])))
