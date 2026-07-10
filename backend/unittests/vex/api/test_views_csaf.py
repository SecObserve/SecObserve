from os import path
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import dateparse
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Observation, Product, Product_Member
from application.licenses.models import License_Component
from application.vex.models import CSAF, CSAF_Branch, CSAF_Revision, CSAF_Vulnerability
from application.vex.types import (
    CSAF_Publisher_Category,
    CSAF_TLP_Label,
    CSAF_Tracking_Status,
)


class TestCSAF(TestCase):
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
    @patch("application.vex.services.csaf_generator.user_has_permission_or_403")
    @patch("application.vex.services.csaf_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_csaf_document_product_no_branch(
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
            "document_id_prefix": "CSAF",
            "title": "Title",
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=csaf_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )

        with open(path.dirname(__file__) + "/files/csaf_product_no_branch.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        csaf = CSAF.objects.get(document_id_prefix="CSAF", document_base_id="2020_0001")
        self.assertEqual(vex_user, csaf.user)
        self.assertEqual(Product.objects.get(id=1), csaf.product)
        self.assertEqual(1, csaf.version)
        self.assertEqual(
            "d95a991952c7a926d90e2beadcbd5d691e740f599df95470f1a4615b0a1d0470",
            csaf.content_hash,
        )
        self.assertEqual("Title", csaf.title)
        self.assertEqual("Publisher", csaf.publisher_name)
        self.assertEqual(
            CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            csaf.publisher_category,
        )
        self.assertEqual("https://vex.example.com", csaf.publisher_namespace)
        self.assertEqual(CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL, csaf.tracking_status)
        self.assertEqual(
            CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
            csaf.tlp_label,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_initial_release_date,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_current_release_date,
        )

        csaf_branches = CSAF_Branch.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_branches))

        csaf_vulnerabilities = CSAF_Vulnerability.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_vulnerabilities))

        csaf_revisions = CSAF_Revision.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_revisions))
        self.assertEqual(dateparse.parse_datetime("2020-01-01T04:30:00Z"), csaf_revisions[0].date)
        self.assertEqual(1, csaf_revisions[0].version)
        self.assertEqual("Initial release", csaf_revisions[0].summary)

        # --- update without changes ---

        parameters = {
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_USER,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_DRAFT,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_AMBER,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/update/CSAF/2020_0001/", parameters, format="json")

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
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_USER,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_DRAFT,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_AMBER,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/update/CSAF/2020_0001/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=csaf_2020_0001_0002.json",
            response.headers["Content-Disposition"],
        )

        with open(path.dirname(__file__) + "/files/csaf_product_no_branch_update.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        csaf = CSAF.objects.get(document_id_prefix="CSAF", document_base_id="2020_0001")
        self.assertEqual(vex_user, csaf.user)
        self.assertEqual(Product.objects.get(id=1), csaf.product)
        self.assertEqual(2, csaf.version)
        self.assertEqual(
            "d4d235a598370dfaa825172c73663acdc5dd5b55b3dc676f6ac22f48a0b7c3fb",
            csaf.content_hash,
        )
        self.assertEqual("Title", csaf.title)
        self.assertEqual("Publisher", csaf.publisher_name)
        self.assertEqual(
            CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_USER,
            csaf.publisher_category,
        )
        self.assertEqual("https://vex.example.com", csaf.publisher_namespace)
        self.assertEqual(CSAF_Tracking_Status.CSAF_TRACKING_STATUS_DRAFT, csaf.tracking_status)
        self.assertEqual(
            CSAF_TLP_Label.CSAF_TLP_LABEL_AMBER,
            csaf.tlp_label,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_initial_release_date,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-02-01T04:30:00Z"),
            csaf.tracking_current_release_date,
        )

        csaf_branches = CSAF_Branch.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_branches))

        csaf_vulnerabilities = CSAF_Vulnerability.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_vulnerabilities))

        csaf_revisions = CSAF_Revision.objects.filter(csaf=csaf)
        self.assertEqual(2, len(csaf_revisions))
        self.assertEqual(dateparse.parse_datetime("2020-02-01T04:30:00Z"), csaf_revisions[1].date)
        self.assertEqual(2, csaf_revisions[1].version)
        self.assertEqual("Update", csaf_revisions[1].summary)

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.csaf_generator.user_has_permission_or_403")
    @patch("application.vex.services.csaf_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_csaf_document_product_branches(
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
            "document_id_prefix": "CSAF",
            "title": "Title",
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=csaf_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )

        with open(path.dirname(__file__) + "/files/csaf_product_branches.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        csaf = CSAF.objects.get(document_id_prefix="CSAF", document_base_id="2020_0001")
        self.assertEqual(vex_user, csaf.user)
        self.assertEqual(Product.objects.get(id=2), csaf.product)
        self.assertEqual(1, csaf.version)
        self.assertEqual(
            "17dcf310dc70fcfde16c7fce6560fa950f8307c15dff66226460f32e6166a8be",
            csaf.content_hash,
        )
        self.assertEqual("Title", csaf.title)
        self.assertEqual("Publisher", csaf.publisher_name)
        self.assertEqual(
            CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            csaf.publisher_category,
        )
        self.assertEqual("https://vex.example.com", csaf.publisher_namespace)
        self.assertEqual(CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL, csaf.tracking_status)
        self.assertEqual(
            CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
            csaf.tlp_label,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_initial_release_date,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_current_release_date,
        )

        csaf_branches = CSAF_Branch.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_branches))

        csaf_vulnerabilities = CSAF_Vulnerability.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_vulnerabilities))

        csaf_revisions = CSAF_Revision.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_revisions))
        self.assertEqual(dateparse.parse_datetime("2020-01-01T04:30:00Z"), csaf_revisions[0].date)
        self.assertEqual(1, csaf_revisions[0].version)
        self.assertEqual("Initial release", csaf_revisions[0].summary)

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.csaf_generator.user_has_permission_or_403")
    @patch("application.vex.services.csaf_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_csaf_document_product_given_branch(
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
            "branches": [2],
            "document_id_prefix": "CSAF",
            "title": "Title",
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=csaf_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )

        with open(path.dirname(__file__) + "/files/csaf_product_given_branch.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        csaf = CSAF.objects.get(document_id_prefix="CSAF", document_base_id="2020_0001")
        self.assertEqual(vex_user, csaf.user)
        self.assertEqual(Product.objects.get(id=2), csaf.product)
        self.assertEqual(1, csaf.version)
        self.assertEqual(
            "7eab73b134c451d9f8a73dbe52346aca0dde97aa3c22ec8cf647a656ab76e25b",
            csaf.content_hash,
        )
        self.assertEqual("Title", csaf.title)
        self.assertEqual("Publisher", csaf.publisher_name)
        self.assertEqual(
            CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            csaf.publisher_category,
        )
        self.assertEqual("https://vex.example.com", csaf.publisher_namespace)
        self.assertEqual(CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL, csaf.tracking_status)
        self.assertEqual(
            CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
            csaf.tlp_label,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_initial_release_date,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_current_release_date,
        )

        csaf_branches = CSAF_Branch.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_branches))
        self.assertEqual(2, csaf_branches[0].branch.pk)

        csaf_vulnerabilities = CSAF_Vulnerability.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_vulnerabilities))

        csaf_revisions = CSAF_Revision.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_revisions))
        self.assertEqual(dateparse.parse_datetime("2020-01-01T04:30:00Z"), csaf_revisions[0].date)
        self.assertEqual(1, csaf_revisions[0].version)
        self.assertEqual("Initial release", csaf_revisions[0].summary)

    @patch("django.utils.timezone.now")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.vex.services.csaf_generator.user_has_permission_or_403")
    @patch("application.vex.services.csaf_generator.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_csaf_document_given_vulnerability(
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
            "document_id_prefix": "CSAF",
            "title": "Title",
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/create/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=csaf_2020_0001_0001.json",
            response.headers["Content-Disposition"],
        )

        with open(path.dirname(__file__) + "/files/csaf_given_vulnerability.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        csaf = CSAF.objects.get(document_id_prefix="CSAF", document_base_id="2020_0001")
        self.assertEqual(vex_user, csaf.user)
        self.assertEqual(None, csaf.product)
        self.assertEqual(1, csaf.version)
        self.assertEqual(
            "e7444a7013ee24938b6757183d76ab87aa49921508bd1a5980fb64ff30b78a2b",
            csaf.content_hash,
        )
        self.assertEqual("Title", csaf.title)
        self.assertEqual("Publisher", csaf.publisher_name)
        self.assertEqual(
            CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_VENDOR,
            csaf.publisher_category,
        )
        self.assertEqual("https://vex.example.com", csaf.publisher_namespace)
        self.assertEqual(CSAF_Tracking_Status.CSAF_TRACKING_STATUS_FINAL, csaf.tracking_status)
        self.assertEqual(
            CSAF_TLP_Label.CSAF_TLP_LABEL_WHITE,
            csaf.tlp_label,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_initial_release_date,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_current_release_date,
        )

        csaf_branches = CSAF_Branch.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_branches))

        csaf_vulnerabilities = CSAF_Vulnerability.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_vulnerabilities))
        self.assertEqual("CVE-vulnerability_2", csaf_vulnerabilities[0].name)

        csaf_revisions = CSAF_Revision.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_revisions))
        self.assertEqual(dateparse.parse_datetime("2020-01-01T04:30:00Z"), csaf_revisions[0].date)
        self.assertEqual(1, csaf_revisions[0].version)
        self.assertEqual("Initial release", csaf_revisions[0].summary)

        # --- update without changes ---

        parameters = {
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_USER,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_DRAFT,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_AMBER,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/update/CSAF/2020_0001/", parameters, format="json")

        self.assertEqual(204, response.status_code)

        # --- update with changes ---

        mock_now.return_value = dateparse.parse_datetime("2020-02-01T04:30:00Z")

        observation_2 = Observation.objects.get(id=2)
        observation_2.current_status = "Open"
        observation_2.assessment_status = ""
        observation_2.save()

        parameters = {
            "publisher_name": "Publisher",
            "publisher_category": CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_USER,
            "publisher_namespace": "https://vex.example.com",
            "tracking_status": CSAF_Tracking_Status.CSAF_TRACKING_STATUS_DRAFT,
            "tlp_label": CSAF_TLP_Label.CSAF_TLP_LABEL_AMBER,
        }

        api_client = APIClient()
        response = api_client.post("/api/vex/csaf_document/update/CSAF/2020_0001/", parameters, format="json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/json", response.headers["Content-Type"])
        self.assertEqual(
            "attachment; filename=csaf_2020_0001_0002.json",
            response.headers["Content-Disposition"],
        )

        with open(path.dirname(__file__) + "/files/csaf_given_vulnerability_update.json", "r") as testfile:
            self.assertEqual(testfile.read(), response._container[0].decode("utf-8"))

        csaf = CSAF.objects.get(document_id_prefix="CSAF", document_base_id="2020_0001")
        self.assertEqual(vex_user, csaf.user)
        self.assertEqual(None, csaf.product)
        self.assertEqual(2, csaf.version)
        self.assertEqual(
            "578b26be2b54431bd004ce9828775023ebcfb45f5365f1daab6c5212061b123b",
            csaf.content_hash,
        )
        self.assertEqual("Title", csaf.title)
        self.assertEqual("Publisher", csaf.publisher_name)
        self.assertEqual(
            CSAF_Publisher_Category.CSAF_PUBLISHER_CATEGORY_USER,
            csaf.publisher_category,
        )
        self.assertEqual("https://vex.example.com", csaf.publisher_namespace)
        self.assertEqual(CSAF_Tracking_Status.CSAF_TRACKING_STATUS_DRAFT, csaf.tracking_status)
        self.assertEqual(
            CSAF_TLP_Label.CSAF_TLP_LABEL_AMBER,
            csaf.tlp_label,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-01-01T04:30:00Z"),
            csaf.tracking_initial_release_date,
        )
        self.assertEqual(
            dateparse.parse_datetime("2020-02-01T04:30:00Z"),
            csaf.tracking_current_release_date,
        )

        csaf_branches = CSAF_Branch.objects.filter(csaf=csaf)
        self.assertEqual(0, len(csaf_branches))

        csaf_vulnerabilities = CSAF_Vulnerability.objects.filter(csaf=csaf)
        self.assertEqual(1, len(csaf_vulnerabilities))
        self.assertEqual("CVE-vulnerability_2", csaf_vulnerabilities[0].name)

        csaf_revisions = CSAF_Revision.objects.filter(csaf=csaf)
        self.assertEqual(2, len(csaf_revisions))
        self.assertEqual(dateparse.parse_datetime("2020-02-01T04:30:00Z"), csaf_revisions[1].date)
        self.assertEqual(2, csaf_revisions[1].version)
        self.assertEqual("Update", csaf_revisions[1].summary)
