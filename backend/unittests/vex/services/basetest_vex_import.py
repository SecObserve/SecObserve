from os import path
from unittest import TestCase

from application.core.models import Observation, Product
from application.core.types import Status, VEX_Justification
from application.import_observations.services.import_observations import (
    FileUploadParameters,
    file_upload_observations,
)
from application.licenses.models import License_Component
from application.vex.models import VEX_Document, VEX_Statement
from application.vex.types import VEX_Document_Type, VEX_Status


class BaseTestVEXImport(TestCase):
    def load_vex_test(self, short: bool = False) -> None:
        purl_vex_test = "pkg:github/SecObserve/VEX_Test" if short else "pkg:github/SecObserve/VEX_Test@v1.7.0"
        product = Product.objects.create(
            purl=purl_vex_test,
            name="VEX_Test",
            description="VEX Test Product",
        )
        filename = "/files/trivy_poetry_short.json" if short else "/files/trivy_poetry.json"
        with open(path.dirname(__file__) + filename) as testfile:
            file_upload_parameter = FileUploadParameters(
                product=product,
                branch=None,
                file=testfile,
                service_name="",
                docker_image_name_tag="",
                endpoint_url="",
                kubernetes_cluster="",
                suppress_licenses=False,
                sbom=False,
            )
            file_upload_observations(file_upload_parameter)

    def tearDown(self):
        VEX_Statement.objects.all().delete()
        VEX_Document.objects.all().delete()
        Observation.objects.filter(product__name="VEX_Test").delete()
        License_Component.objects.filter(product__name="VEX_Test").delete()
        Product.objects.filter(name="VEX_Test").delete()

    def check_vex_document(self, vex_document: VEX_Document, document_type: str, short: bool = False) -> None:
        self.assertEqual(document_type, vex_document.type)
        self.assertEqual("1", vex_document.version)

        if document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF:
            self.assertEqual("vendor", vex_document.role)
            self.assertEqual("2024-07-14T11:12:19.671904+00:00", vex_document.initial_release_date.isoformat())
            self.assertEqual("2024-07-14T11:12:19.671919+00:00", vex_document.current_release_date.isoformat())
        elif document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_OPENVEX:
            self.assertEqual("vendor", vex_document.role)
            self.assertEqual("2024-07-14T11:17:57.668593+00:00", vex_document.initial_release_date.isoformat())
            self.assertEqual("2024-07-14T11:17:57.668609+00:00", vex_document.current_release_date.isoformat())
        elif document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_CYCLONEDX:
            self.assertEqual("", vex_document.role)
            self.assertEqual("2024-07-14T11:17:57.668593+00:00", vex_document.initial_release_date.isoformat())
            self.assertEqual("2024-07-14T11:17:57.668593+00:00", vex_document.current_release_date.isoformat())

        vex_statements = VEX_Statement.objects.filter(document=vex_document)
        self.assertEqual(13, len(vex_statements))

        found_49083 = False
        found_0727 = False
        found_4340 = False

        purl_vex_test = "pkg:github/SecObserve/VEX_Test" if short else "pkg:github/SecObserve/VEX_Test@v1.7.0"
        purl_cryptography = "pkg:pypi/cryptography" if short else "pkg:pypi/cryptography@41.0.5"
        purl_sqlparse = "pkg:pypi/sqlparse" if short else "pkg:pypi/sqlparse@0.4.4"

        for vex_statement in vex_statements:
            if vex_statement.vulnerability_id == "CVE-2023-49083" and (
                (
                    vex_statement.component_purl
                    and vex_statement.component_purl == purl_cryptography
                    or (
                        vex_statement.component_cyclonedx_bom_link
                        and vex_statement.component_cyclonedx_bom_link
                        == "urn:cdx:aebccdfe-fab4-4210-acce-bac771d4842d/1#pkg:pypi/cryptography@41.0.5"
                    )
                )
            ):
                found_49083 = True
                self.assertTrue(
                    vex_statement.description.startswith(
                        "cryptography is a package designed to expose cryptographic primitives and recipes to Python developers."
                    )
                )
                self.assertEqual(VEX_Status.VEX_STATUS_NOT_AFFECTED, vex_statement.status)
                self.assertIn(
                    vex_statement.justification,
                    [
                        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,
                        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION,
                    ],
                )
                if document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF:
                    self.assertEqual("", vex_statement.impact)
                else:
                    self.assertEqual("Not affected for VEX test case", vex_statement.impact)

                self.assertEqual("", vex_statement.remediation)
                if vex_statement.component_cyclonedx_bom_link:
                    self.assertEqual("", vex_statement.product_purl)
                else:
                    self.assertEqual(
                        purl_vex_test,
                        vex_statement.product_purl,
                    )

            if vex_statement.vulnerability_id == "CVE-2024-0727" and (
                (vex_statement.component_purl and vex_statement.component_purl == purl_cryptography)
                or (
                    vex_statement.component_cyclonedx_bom_link
                    and vex_statement.component_cyclonedx_bom_link
                    == "urn:cdx:aebccdfe-fab4-4210-acce-bac771d4842d/1#pkg:pypi/cryptography@41.0.5"
                )
            ):
                found_0727 = True
                self.assertTrue(
                    vex_statement.description.startswith(
                        "Issue summary: Processing a maliciously formatted PKCS12 file"
                    )
                )
                self.assertEqual(VEX_Status.VEX_STATUS_AFFECTED, vex_statement.status)
                self.assertEqual(
                    "",
                    vex_statement.justification,
                )
                self.assertEqual("", vex_statement.impact)
                self.assertEqual("Upgrade cryptography to version 42.0.2", vex_statement.remediation)
                if vex_statement.component_cyclonedx_bom_link:
                    self.assertEqual("", vex_statement.product_purl)
                else:
                    self.assertEqual(
                        purl_vex_test,
                        vex_statement.product_purl,
                    )

            if vex_statement.vulnerability_id == "CVE-2024-4340" and (
                (vex_statement.component_purl and vex_statement.component_purl == purl_sqlparse)
                or (
                    vex_statement.component_cyclonedx_bom_link
                    and vex_statement.component_cyclonedx_bom_link
                    == "urn:cdx:aebccdfe-fab4-4210-acce-bac771d4842d/1#pkg:pypi/sqlparse@0.4.4"
                )
            ):
                found_4340 = True
                self.assertTrue(
                    vex_statement.description.startswith("Passing a heavily nested list to sqlparse.parse()")
                )
                self.assertEqual(VEX_Status.VEX_STATUS_UNDER_INVESTIGATION, vex_statement.status)
                self.assertEqual(
                    "",
                    vex_statement.justification,
                )
                self.assertEqual("", vex_statement.impact)
                self.assertEqual("", vex_statement.remediation)
                if vex_statement.component_cyclonedx_bom_link:
                    self.assertEqual("", vex_statement.product_purl)
                else:
                    self.assertEqual(
                        purl_vex_test,
                        vex_statement.product_purl,
                    )

        self.assertTrue(found_49083)
        self.assertTrue(found_0727)
        self.assertTrue(found_4340)

    def check_vex_document_without_component_purl(
        self, vex_document: VEX_Document, document_type: str, short: bool = False
    ) -> None:
        self.assertEqual(document_type, vex_document.type)
        self.assertEqual("1", vex_document.version)

        if document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF:
            self.assertEqual("vendor", vex_document.role)
            self.assertEqual("2024-07-14T11:12:19.671904+00:00", vex_document.initial_release_date.isoformat())
            self.assertEqual("2024-07-14T11:12:19.671919+00:00", vex_document.current_release_date.isoformat())
        elif document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_OPENVEX:
            self.assertEqual("vendor", vex_document.role)
            self.assertEqual("2024-07-14T11:17:57.668593+00:00", vex_document.initial_release_date.isoformat())
            self.assertEqual("2024-07-14T11:17:57.668609+00:00", vex_document.current_release_date.isoformat())

        vex_statements = VEX_Statement.objects.filter(document=vex_document)
        self.assertEqual(13, len(vex_statements))

        for vex_statement in vex_statements:
            self.assertEqual("", vex_statement.component_purl)
            self.assertEqual("", vex_statement.component_cyclonedx_bom_link)

        purl_cryptography = "pkg:pypi/cryptography" if short else "pkg:pypi/cryptography@41.0.5"
        purl_sqlparse = "pkg:pypi/sqlparse" if short else "pkg:pypi/sqlparse@0.4.4"

        found_49083 = False
        found_0727 = False
        found_4340 = False

        for vex_statement in vex_statements:
            if vex_statement.vulnerability_id == "CVE-2023-49083":
                found_49083 = True
                self.assertTrue(
                    vex_statement.description.startswith(
                        "cryptography is a package designed to expose cryptographic primitives and recipes to Python developers."
                    )
                )
                self.assertEqual(VEX_Status.VEX_STATUS_NOT_AFFECTED, vex_statement.status)
                self.assertEqual(
                    VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,
                    vex_statement.justification,
                )
                if document_type == VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF:
                    self.assertEqual("", vex_statement.impact)
                else:
                    self.assertEqual("Not affected for VEX test case", vex_statement.impact)
                self.assertEqual("", vex_statement.remediation)
                self.assertEqual(purl_cryptography, vex_statement.product_purl)

            if vex_statement.vulnerability_id == "CVE-2024-0727":
                found_0727 = True
                self.assertTrue(
                    vex_statement.description.startswith(
                        "Issue summary: Processing a maliciously formatted PKCS12 file"
                    )
                )
                self.assertEqual(VEX_Status.VEX_STATUS_AFFECTED, vex_statement.status)
                self.assertEqual("", vex_statement.justification)
                self.assertEqual("", vex_statement.impact)
                self.assertEqual("Upgrade cryptography to version 42.0.2", vex_statement.remediation)
                self.assertEqual(purl_cryptography, vex_statement.product_purl)

            if vex_statement.vulnerability_id == "CVE-2024-4340":
                found_4340 = True
                self.assertTrue(
                    vex_statement.description.startswith("Passing a heavily nested list to sqlparse.parse()")
                )
                self.assertEqual(VEX_Status.VEX_STATUS_UNDER_INVESTIGATION, vex_statement.status)
                self.assertEqual("", vex_statement.justification)
                self.assertEqual("", vex_statement.impact)
                self.assertEqual("", vex_statement.remediation)
                self.assertEqual(purl_sqlparse, vex_statement.product_purl)

        self.assertTrue(found_49083)
        self.assertTrue(found_0727)
        self.assertTrue(found_4340)

    def check_product(self, short: bool = False) -> None:
        purl_vex_test = "pkg:github/SecObserve/VEX_Test" if short else "pkg:github/SecObserve/VEX_Test@v1.7.0"
        purl_cryptography = "pkg:pypi/cryptography" if short else "pkg:pypi/cryptography@41.0.5"
        purl_sqlparse = "pkg:pypi/sqlparse" if short else "pkg:pypi/sqlparse@0.4.4"

        product = Product.objects.get(purl=purl_vex_test)
        observations = Observation.objects.filter(product=product, current_status=Status.STATUS_AFFECTED)
        self.assertEqual(11, len(observations))

        observation = Observation.objects.get(
            product=product,
            vulnerability_id="CVE-2023-49083",
            origin_component_purl=purl_cryptography,
        )
        self.assertEqual(Status.STATUS_NOT_AFFECTED, observation.current_status)
        self.assertEqual(Status.STATUS_NOT_AFFECTED, observation.vex_status)
        self.assertIn(
            observation.current_vex_justification,
            [
                VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,
                VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION,
            ],
        )
        self.assertIn(
            observation.vex_vex_justification,
            [
                VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,
                VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION,
            ],
        )

        observation = Observation.objects.get(
            product=product,
            vulnerability_id="CVE-2024-4340",
            origin_component_purl=purl_sqlparse,
        )
        self.assertEqual(Status.STATUS_IN_REVIEW, observation.current_status)
        self.assertEqual(Status.STATUS_IN_REVIEW, observation.vex_status)
        self.assertEqual("", observation.current_vex_justification)
        self.assertEqual("", observation.vex_vex_justification)
