import copy
import io
import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from application.access_control.models import User
from application.vex.models import VEX_Document, VEX_Statement
from application.vex.services.vex_import import import_vex
from unittests.base_test_case import BaseTestCase

CYCLONEDX_DOCUMENT = {
    "bomFormat": "CycloneDX",
    "serialNumber": "urn:uuid:0e3c2a41-8f5b-4a8e-9a57-3a1c0c3e2d10",
    "version": 1,
    "metadata": {
        "authors": [{"name": "author"}],
        "component": {"type": "library", "name": "dash", "purl": "pkg:deb/ubuntu/dash"},
    },
    "vulnerabilities": [{"id": "CVE-2026-0001", "analysis": {"state": "false_positive", "detail": "detail"}}],
}

OPENVEX_DOCUMENT = {
    "@context": "https://openvex.dev/ns/v0.2.0",
    "@id": "https://example.com/vex/1",
    "author": "author",
    "timestamp": "2026-09-28T00:00:00Z",
    "version": 1,
    "statements": [
        {
            "vulnerability": {"name": "CVE-2026-0001"},
            "products": [{"@id": "pkg:deb/ubuntu/dash"}],
            "status": "not_affected",
            "impact_statement": "impact",
        }
    ],
}


def _cyclonedx(**analysis: str) -> dict:
    document = copy.deepcopy(CYCLONEDX_DOCUMENT)
    document["vulnerabilities"][0]["analysis"].update(analysis)
    return document


class TestVEXImportValidation(BaseTestCase):
    def _import(self, document: dict) -> str:
        with self.assertRaises(ValidationError) as e:
            import_vex(io.StringIO(json.dumps(document)))
        return str(e.exception.detail[0])

    def test_cyclonedx_statement_too_long(self):
        message = self._import(_cyclonedx(detail="x" * 256))

        self.assertEqual(
            "VEX statement for CVE-2026-0001: impact: Ensure this value has at most 255 characters (it has 256).",
            message,
        )

    def test_cyclonedx_statement_invalid_justification(self):
        message = self._import(_cyclonedx(state="not_affected", justification="not_a_justification"))

        self.assertEqual(
            "VEX statement for CVE-2026-0001: justification: Value 'not_a_justification' is not a valid choice.",
            message,
        )

    def test_cyclonedx_document_too_long(self):
        document = copy.deepcopy(CYCLONEDX_DOCUMENT)
        document["metadata"]["authors"][0]["name"] = "a" * 256

        message = self._import(document)

        self.assertEqual(
            "VEX document urn:uuid:0e3c2a41-8f5b-4a8e-9a57-3a1c0c3e2d10: "
            "author: Ensure this value has at most 255 characters (it has 256).",
            message,
        )

    def test_openvex_statement_too_long(self):
        document = copy.deepcopy(OPENVEX_DOCUMENT)
        document["statements"][0]["impact_statement"] = "x" * 256

        message = self._import(document)

        self.assertEqual(
            "VEX statement for CVE-2026-0001: impact: Ensure this value has at most 255 characters (it has 256).",
            message,
        )

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_api_rejected_import_keeps_previous_document(self, mock_authenticate):
        mock_authenticate.return_value = User.objects.create(username="superuser@example.com", is_superuser=True), None
        api_client = APIClient()

        def upload(document: dict):
            file = SimpleUploadedFile("vex.json", json.dumps(document).encode(), content_type="application/json")
            return api_client.post("/api/vex/vex_import/", {"file": file}, format="multipart")

        self.assertEqual(204, upload(CYCLONEDX_DOCUMENT).status_code)
        response = upload(_cyclonedx(detail="x" * 256))

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "message": "VEX statement for CVE-2026-0001: impact: "
                "Ensure this value has at most 255 characters (it has 256)."
            },
            response.data,
        )
        self.assertEqual(1, VEX_Document.objects.count())
        self.assertEqual(["detail"], list(VEX_Statement.objects.values_list("impact", flat=True)))
