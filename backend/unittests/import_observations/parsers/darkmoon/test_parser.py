from json import dumps
from os import path
from unittest import TestCase

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.darkmoon.parser import DarkmoonParser
from application.import_observations.services.parser_detector import detect_parser


class TestDarkmoonParser(TestCase):
    def test_darkmoon(self):
        with open(path.dirname(__file__) + "/files/darkmoon.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("Darkmoon", parser.name)
            self.assertEqual("DAST", parser.type)
            self.assertIsInstance(parser_instance, DarkmoonParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Darkmoon", scanner)
            self.assertEqual(3, len(observations))

            observation = observations[0]
            self.assertEqual("Unauthenticated remote code execution in file upload handler", observation.title)
            self.assertEqual(Severity.SEVERITY_CRITICAL, observation.parser_severity)
            self.assertEqual("Darkmoon", observation.scanner)
            self.assertEqual("https://app.example.test/upload", observation.origin_endpoint_url)
            self.assertEqual("CVE-2026-12345", observation.vulnerability_id)
            self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", observation.cvss3_vector)
            self.assertEqual("", observation.cvss4_vector)
            self.assertEqual(
                "Validate and normalise uploaded filenames, store uploads outside the web root and disable script execution in the upload directory.",
                observation.recommendation,
            )
            description = """The /upload endpoint writes the client supplied filename to disk without sanitisation, which allows a PHP web shell to be dropped and executed.

**Exploitation status:** Exploited (proven with a working exploit)

**Category:** remote_code_execution

**Discovered by agent:** php

**Plugin or component:** upload-handler

**MITRE ATT&CK:** T1190 (Exploit Public-Facing Application)

**ISO 27001 control:** A.8.26

**Evidence:** A PHP web shell was uploaded and executed with the id command, confirming code execution as www-data."""
            self.assertEqual(description, observation.description)
            self.assertEqual(
                [
                    "https://nvd.nist.gov/vuln/detail/CVE-2026-12345",
                    "https://attack.mitre.org/techniques/T1190/",
                ],
                observation.unsaved_references,
            )
            self.assertEqual(4, len(observation.unsaved_evidences))
            self.assertEqual("Commands", observation.unsaved_evidences[0][0])
            self.assertIn("curl -s -F", observation.unsaved_evidences[0][1])
            self.assertEqual("Logs", observation.unsaved_evidences[1][0])
            self.assertEqual("Request", observation.unsaved_evidences[2][0])
            self.assertEqual("Response", observation.unsaved_evidences[3][0])

            observation = observations[1]
            self.assertEqual(Severity.SEVERITY_HIGH, observation.parser_severity)
            self.assertIn("**Exploitation status:** Confirmed\n", observation.description)
            self.assertEqual(
                ["https://attack.mitre.org/techniques/T1059/007/"],
                observation.unsaved_references,
            )

            observation = observations[2]
            self.assertEqual("Server-side request forgery in URL preview feature", observation.title)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)
            self.assertEqual("", observation.cvss3_vector)
            self.assertEqual("", observation.vulnerability_id)
            self.assertIn("**Exploitation status:** Unconfirmed", observation.description)
            self.assertIn("**CVSS score:** 6.5", observation.description)
            self.assertEqual([], observation.unsaved_references)
            self.assertEqual("Finding", observation.unsaved_evidences[0][0])

    def test_check_format_list_of_findings(self):
        parser = DarkmoonParser()
        finding = {"title": "Finding", "status": "exploited", "discovered_by_agent": "php"}

        self.assertTrue(parser.check_format([finding]))
        self.assertTrue(parser.check_format({"findings": [finding]}))

    def test_check_format_rejects_other_formats(self):
        parser = DarkmoonParser()

        self.assertFalse(parser.check_format({"findings": []}))
        self.assertFalse(parser.check_format([]))
        self.assertFalse(parser.check_format({"findings": [{"RuleID": "x", "Match": "y", "Secret": "z"}]}))
        self.assertFalse(parser.check_format([{"title": "Finding", "severity": "high"}]))
        self.assertFalse(parser.check_format({"format": "SecObserve"}))
        self.assertFalse(parser.check_format("Darkmoon"))

    def test_invalid_cvss_vector_is_ignored(self):
        parser = DarkmoonParser()
        data = [
            {
                "title": "Finding",
                "severity": "low",
                "status": "confirmed",
                "discovered_by_agent": "php",
                "cvss_vector": "CVSS:3.1/AV:X",
                "cvss_score": 3.1,
            }
        ]

        observations, _ = parser.get_observations(data, Product(name="product"), None)

        self.assertEqual("", observations[0].cvss3_vector)
        self.assertEqual(Severity.SEVERITY_LOW, observations[0].parser_severity)
        self.assertIn("**CVSS score:** 3.1", observations[0].description)

    def test_cvss4_vector(self):
        parser = DarkmoonParser()
        vector = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
        data = [
            {
                "title": "Finding",
                "severity": "critical",
                "status": "exploited",
                "discovered_by_agent": "php",
                "cvss_vector": vector,
            }
        ]

        observations, _ = parser.get_observations(data, Product(name="product"), None)

        self.assertEqual(vector, observations[0].cvss4_vector)
        self.assertEqual("", observations[0].cvss3_vector)

    def test_long_title_is_truncated(self):
        parser = DarkmoonParser()
        data = [{"title": "x" * 400, "severity": "info", "status": "unconfirmed", "discovered_by_agent": "php"}]

        observations, _ = parser.get_observations(data, Product(name="product"), None)

        self.assertEqual(255, len(observations[0].title))
        self.assertEqual(Severity.SEVERITY_NONE, observations[0].parser_severity)
        self.assertEqual(dumps(data[0]), observations[0].unsaved_evidences[0][1])
