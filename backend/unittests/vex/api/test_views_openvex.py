from os import path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import dateparse
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Branch, Observation, Product, Product_Member
from application.licenses.models import License_Component
from application.vex.models import OpenVEX, OpenVEX_Branch, OpenVEX_Vulnerability


class TestOpenVEX(TestCase):
    def setUp(self):
        Observation.objects.all().delete()
        License_Component.objects.all().delete()
        Product.objects.filter(is_product_group=False).delete()
        Product.objects.all().delete()
        Product_Member.objects.all().delete()
        User.objects.all().delete()

        call_command("loaddata", "unittests/fixtures/vex_fixtures.json")

        self.maxDiff = None

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.openvex_generator.user_has_permission_or_403")
    @patch("application.vex.services.openvex_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_openvex_document_product_no_branch(
        self,
        mock_get_current_user_1,
        mock_get_current_user_2,
        mock_get_user_has_permission_or_403,
        mock_authenticate,
        mock_now,
    ):
        mock_now.return_value = dateparse.parse_datetime("2020-01-01T04:30:00Z")
        vex_user = User.objects.get(username="vex_user")
        mock_authenticate.return_value = vex_user, None
        mock_get_current_user_1.return_value = vex_user
        mock_get_current_user_2.return_value = vex_user

        # --- create ---

        parameters = {
            "product": 1,
            "document_id_prefix": "OpenVEX",
            "id_namespace": "https://vex.example.com",
            "author": "Author",
            "role": "Role",
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/openvex_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )
        with open(path.dirname(__file__) + "/files/openvex_product_no_branch.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        openvex = OpenVEX.objects.get(document_id_prefix="OpenVEX", document_base_id="2020_0001")
        self.assertEqual(vex_user, openvex.user)
        self.assertEqual(Product.objects.get(id=1), openvex.product)
        self.assertEqual(1, openvex.version)
        self.assertEqual(
            "2349866f922095e32c824029bffedd6a5d3a94fb48385879840542cee7a8528f",
            openvex.content_hash,
        )
        self.assertEqual("https://vex.example.com", openvex.id_namespace)
        self.assertEqual("Author", openvex.author)
        self.assertEqual("Role", openvex.role)
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.timestamp,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.last_updated,
        )

        openvex_branches = OpenVEX_Branch.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_branches))

        openvex_vulnerabilities = OpenVEX_Vulnerability.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_vulnerabilities))

        # --- update without changes ---

        parameters = {
            "author": "New Author",
            "role": "New Role",
        }

        api_client = APIClient()
        response = api_client.post(
            "/api/vex/openvex_document/update/OpenVEX/2020_0001/",
            parameters,
            format="json",
        )

        self.assertEqual(204, response.status_code)

        # --- update with changes ---

        mock_now.return_value = dateparse.parse_datetime("2020-02-01T04:30:00Z")

        observation_1 = Observation.objects.get(id=1)
        observation_1.description = "new description"
        observation_1.save()

        observation_2 = Observation.objects.get(id=2)
        observation_2.current_status = "Open"
        observation_2.assessment_status = ""
        observation_2.save()

        parameters = {
            "author": "New Author",
            "role": "New Role",
        }

        api_client = APIClient()
        response = api_client.post(
            "/api/vex/openvex_document/update/OpenVEX/2020_0001/",
            parameters,
            format="json",
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0002.json",
            response.headers["Content-Disposition"],
        )
        with open(path.dirname(__file__) + "/files/openvex_product_no_branch_update.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        openvex = OpenVEX.objects.get(document_id_prefix="OpenVEX", document_base_id="2020_0001")
        self.assertEqual(vex_user, openvex.user)
        self.assertEqual(Product.objects.get(id=1), openvex.product)
        self.assertEqual(2, openvex.version)
        self.assertEqual(
            "eb2c932985b9f3100a175f9d1640162aa073af950a2275220fbe1d7edafbfb53",
            openvex.content_hash,
        )
        self.assertEqual("https://vex.example.com", openvex.id_namespace)
        self.assertEqual("New Author", openvex.author)
        self.assertEqual("New Role", openvex.role)
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.timestamp,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-02-01T04:30:00Z"),
            openvex.last_updated,
        )

        openvex_branches = OpenVEX_Branch.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_branches))

        openvex_vulnerabilities = OpenVEX_Vulnerability.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_vulnerabilities))

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.openvex_generator.user_has_permission_or_403")
    @patch("application.vex.services.openvex_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_openvex_document_product_branches(
        self,
        mock_get_current_user_1,
        mock_get_current_user_2,
        mock_get_user_has_permission_or_403,
        mock_authenticate,
        mock_now,
    ):
        mock_now.return_value = dateparse.parse_datetime("2020-01-01T04:30:00Z")
        vex_user = User.objects.get(username="vex_user")
        mock_authenticate.return_value = vex_user, None
        mock_get_current_user_1.return_value = vex_user
        mock_get_current_user_2.return_value = vex_user

        parameters = {
            "product": 2,
            "document_id_prefix": "OpenVEX",
            "id_namespace": "https://vex.example.com",
            "author": "Author",
            "role": "Role",
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/openvex_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )
        with open(path.dirname(__file__) + "/files/openvex_product_branches.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        openvex = OpenVEX.objects.get(document_id_prefix="OpenVEX", document_base_id="2020_0001")
        self.assertEqual(vex_user, openvex.user)
        self.assertEqual(Product.objects.get(id=2), openvex.product)
        self.assertEqual(1, openvex.version)
        self.assertEqual(
            "881f388d3f22c81060697db0af4660cbf787f95567414572e3fbc3807ce10309",
            openvex.content_hash,
        )
        self.assertEqual("https://vex.example.com", openvex.id_namespace)
        self.assertEqual("Author", openvex.author)
        self.assertEqual("Role", openvex.role)
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.timestamp,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.last_updated,
        )

        openvex_branches = OpenVEX_Branch.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_branches))

        openvex_vulnerabilities = OpenVEX_Vulnerability.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_vulnerabilities))

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.openvex_generator.user_has_permission_or_403")
    @patch("application.vex.services.openvex_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_openvex_document_product_same_statement_on_multiple_branches(
        self,
        mock_get_current_user_1,
        mock_get_current_user_2,
        mock_get_user_has_permission_or_403,
        mock_authenticate,
        mock_now,
    ):
        mock_now.return_value = dateparse.parse_datetime("2020-01-01T04:30:00Z")
        vex_user = User.objects.get(username="vex_user")
        mock_authenticate.return_value = vex_user, None
        mock_get_current_user_1.return_value = vex_user
        mock_get_current_user_2.return_value = vex_user

        # same vulnerability with the same status on a second branch
        observation = Observation.objects.get(id=4)
        observation.pk = None
        observation.branch = Branch.objects.get(id=2)
        observation.save()

        parameters = {
            "product": 2,
            "document_id_prefix": "OpenVEX",
            "id_namespace": "https://vex.example.com",
            "author": "Author",
            "role": "Role",
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/openvex_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )
        with open(
            path.dirname(__file__) + "/files/openvex_product_same_statement_on_multiple_branches.json",
            "r",
        ) as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.openvex_generator.user_has_permission_or_403")
    @patch("application.vex.services.openvex_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_openvex_document_product_given_branch(
        self,
        mock_get_current_user_1,
        mock_get_current_user_2,
        mock_get_user_has_permission_or_403,
        mock_authenticate,
        mock_now,
    ):
        mock_now.return_value = dateparse.parse_datetime("2020-01-01T04:30:00Z")
        vex_user = User.objects.get(username="vex_user")
        mock_authenticate.return_value = vex_user, None
        mock_get_current_user_1.return_value = vex_user
        mock_get_current_user_2.return_value = vex_user

        parameters = {
            "product": 2,
            "branch_names": ["main"],
            "document_id_prefix": "OpenVEX",
            "id_namespace": "https://vex.example.com",
            "author": "Author",
            "role": "Role",
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/openvex_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )
        with open(path.dirname(__file__) + "/files/openvex_product_given_branch.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        openvex = OpenVEX.objects.get(document_id_prefix="OpenVEX", document_base_id="2020_0001")
        self.assertEqual(vex_user, openvex.user)
        self.assertEqual(Product.objects.get(id=2), openvex.product)
        self.assertEqual(1, openvex.version)
        self.assertEqual(
            "6a23e9f89f7128b0af35856153657ad7368e1311989a5cce0885e54da4ce7bd2",
            openvex.content_hash,
        )
        self.assertEqual("https://vex.example.com", openvex.id_namespace)
        self.assertEqual("Author", openvex.author)
        self.assertEqual("Role", openvex.role)
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.timestamp,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.last_updated,
        )

        openvex_branches = OpenVEX_Branch.objects.filter(openvex=openvex)
        self.assertEqual(1, len(openvex_branches))
        self.assertEqual(2, openvex_branches[0].branch.pk)

        openvex_vulnerabilities = OpenVEX_Vulnerability.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_vulnerabilities))

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.openvex_generator.user_has_permission_or_403")
    @patch("application.vex.services.openvex_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_openvex_document_given_vulnerability(
        self,
        mock_get_current_user_1,
        mock_get_current_user_2,
        mock_get_user_has_permission_or_403,
        mock_authenticate,
        mock_now,
    ):
        mock_now.return_value = dateparse.parse_datetime("2020-01-01T04:30:00Z")
        vex_user = User.objects.get(username="vex_user")
        mock_authenticate.return_value = vex_user, None
        mock_get_current_user_1.return_value = vex_user
        mock_get_current_user_2.return_value = vex_user

        parameters = {
            "vulnerability_names": ["CVE-vulnerability_2"],
            "document_id_prefix": "OpenVEX",
            "id_namespace": "https://vex.example.com",
            "author": "Author",
            "role": "Role",
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/openvex_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )
        with open(path.dirname(__file__) + "/files/openvex_given_vulnerability.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        openvex = OpenVEX.objects.get(document_id_prefix="OpenVEX", document_base_id="2020_0001")
        self.assertEqual(vex_user, openvex.user)
        self.assertEqual(None, openvex.product)
        self.assertEqual(1, openvex.version)
        self.assertEqual(
            "06008cc75b1a9fdf51bbd7e876c2be85ed0cf4d0162947c9bca3068267f340c4",
            openvex.content_hash,
        )
        self.assertEqual("https://vex.example.com", openvex.id_namespace)
        self.assertEqual("Author", openvex.author)
        self.assertEqual("Role", openvex.role)
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.timestamp,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.last_updated,
        )

        openvex_branches = OpenVEX_Branch.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_branches))

        openvex_vulnerabilities = OpenVEX_Vulnerability.objects.filter(openvex=openvex)
        self.assertEqual(1, len(openvex_vulnerabilities))
        self.assertEqual("CVE-vulnerability_2", openvex_vulnerabilities[0].name)

        # --- update without changes ---

        parameters = {
            "author": "New Author",
            "role": "New Role",
        }

        api_client = APIClient()
        response = api_client.post(
            "/api/vex/openvex_document/update/OpenVEX/2020_0001/",
            parameters,
            format="json",
        )

        self.assertEqual(204, response.status_code)

        # --- update with changes ---

        mock_now.return_value = dateparse.parse_datetime("2020-02-01T04:30:00Z")

        observation_2 = Observation.objects.get(id=2)
        observation_2.current_status = "Open"
        observation_2.assessment_status = ""
        observation_2.save()

        parameters = {
            "author": "New Author",
            "role": "New Role",
        }

        api_client = APIClient()
        response = api_client.post(
            "/api/vex/openvex_document/update/OpenVEX/2020_0001/",
            parameters,
            format="json",
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=OpenVEX_2020_0001_0002.json",
            response.headers["Content-Disposition"],
        )
        with open(
            path.dirname(__file__) + "/files/openvex_given_vulnerability_update.json",
            "r",
        ) as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        openvex = OpenVEX.objects.get(document_id_prefix="OpenVEX", document_base_id="2020_0001")
        self.assertEqual(vex_user, openvex.user)
        self.assertEqual(None, openvex.product)
        self.assertEqual(2, openvex.version)
        self.assertEqual(
            "8e6638435007780014a05d1b8a568db18a50c16ebc89f8bab32a08a87b0ea4ba",
            openvex.content_hash,
        )
        self.assertEqual("https://vex.example.com", openvex.id_namespace)
        self.assertEqual("New Author", openvex.author)
        self.assertEqual("New Role", openvex.role)
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            openvex.timestamp,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-02-01T04:30:00Z"),
            openvex.last_updated,
        )

        openvex_branches = OpenVEX_Branch.objects.filter(openvex=openvex)
        self.assertEqual(0, len(openvex_branches))

        openvex_vulnerabilities = OpenVEX_Vulnerability.objects.filter(openvex=openvex)
        self.assertEqual(1, len(openvex_vulnerabilities))
        self.assertEqual("CVE-vulnerability_2", openvex_vulnerabilities[0].name)
