from json import load
from os import path
from unittest import TestCase

from rest_framework.exceptions import ValidationError

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.gitleaks.parser import GitleaksParser
from application.import_observations.services.parser_detector import detect_parser


class TestGitleaksParser(TestCase):
    def test_no_observations(self):
        with open(path.dirname(__file__) + "/files/gitleaks.empty.json") as testfile:
            parser = GitleaksParser()
            data = load(testfile)

            self.assertTrue(parser.check_format(data))

    def test_gitleaks_dir(self):
        with open(path.dirname(__file__) + "/files/gitleaks.dir.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("Gitleaks", parser.name)
            self.assertIsInstance(parser_instance, GitleaksParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Gitleaks", scanner)
            self.assertEqual(3, len(observations))

            observation = observations[0]
            self.assertEqual("generic-api-key", observation.title)
            description = """Detected a Generic API Key, potentially exposing access to various services and sensitive operations.

**Match:** `DJANGO_SECRET_KEY=REDACTED`"""
            self.assertEqual(description, observation.description)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)

            self.assertEqual("backend/bin/run_pylint.sh", observation.origin_source_file)
            self.assertEqual(18, observation.origin_source_line_start)
            self.assertEqual(19, observation.origin_source_line_end)

            self.assertEqual("Entry", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"Entropy": 5.152115',
                observation.unsaved_evidences[0][1],
            )

    def test_gitleaks_git(self):
        with open(path.dirname(__file__) + "/files/gitleaks.git.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("Gitleaks", parser.name)
            self.assertIsInstance(parser_instance, GitleaksParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Gitleaks", scanner)
            self.assertEqual(3, len(observations))

            observation = observations[0]
            self.assertEqual("generic-api-key", observation.title)
            description = """Detected a Generic API Key, potentially exposing access to various services and sensitive operations.

**Match:** `DJANGO_SECRET_KEY: REDACTED`

**Commit hash:** b718aa975b79d141225d928ba2822ea010b74d2b

**Commit date:** 2023-09-22T07:53:30Z

**Commit message:** chore: switch from cypress to playwright (#568) ..."""
            self.assertEqual(description, observation.description)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)

            self.assertEqual("docker-compose-playwright.yml", observation.origin_source_file)
            self.assertEqual(42, observation.origin_source_line_start)
            self.assertEqual(43, observation.origin_source_line_end)
            self.assertEqual(
                "https://github.com/SecObserve/SecObserve/blob/b718aa975b79d141225d928ba2822ea010b74d2b/docker-compose-playwright.yml#L42",
                observation.origin_source_file_link,
            )

            self.assertEqual("Entry", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"Entropy": 5.152115',
                observation.unsaved_evidences[0][1],
            )

            observation = observations[2]
            description = """Detected a Generic API Key, potentially exposing access to various services and sensitive operations.

**Match:** `DJANGO_SECRET_KEY: REDACTED`

**Commit hash:** a22291a13233b1282ddd0e54e479385690c06fa5

**Commit date:** 2023-09-21T20:15:21Z

**Commit message:** chore: switch from cypress to playwright"""
            self.assertEqual(description, observation.description)
