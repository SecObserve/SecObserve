from json import load
from os import path
from unittest import TestCase

from rest_framework.exceptions import ValidationError

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.betterleaks.parser import BetterleaksParser
from application.import_observations.services.parser_detector import detect_parser


class TestBetterleaksParser(TestCase):
    def test_betterleaks_dir(self):
        with open(path.dirname(__file__) + "/files/betterleaks.dir.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("Betterleaks", parser.name)
            self.assertIsInstance(parser_instance, BetterleaksParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Betterleaks", scanner)
            self.assertEqual(4, len(observations))

            observation = observations[0]
            self.assertEqual("generic-api-key", observation.title)
            description = """Detected a Generic API Key, potentially exposing access to various services and sensitive operations.

**Match:** `DJANGO_SECRET_KEY=REDACTED`"""
            self.assertEqual(description, observation.description)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)

            self.assertEqual("backend/bin/run_pylint.sh", observation.origin_source_file)
            self.assertEqual(18, observation.origin_source_line_start)
            self.assertEqual(18, observation.origin_source_line_end)

            self.assertEqual("Entry", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"Entropy": 5.152115',
                observation.unsaved_evidences[0][1],
            )

    def test_betterleaks_git(self):
        with open(path.dirname(__file__) + "/files/betterleaks.git.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("Betterleaks", parser.name)
            self.assertIsInstance(parser_instance, BetterleaksParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Betterleaks", scanner)
            self.assertEqual(4, len(observations))

            observation = observations[0]
            self.assertEqual("generic-api-key", observation.title)
            description = """Detected a Generic API Key, potentially exposing access to various services and sensitive operations.

**Match:** `DJANGO_SECRET_KEY=REDACTED`

**Commit hash:** 66122e6cbd0b7a7afaac29429da62bc63ee846ea

**Commit date:** 2023-04-11T17:55:00Z

**Commit message:** chore: code quality with pylint (#105)"""
            self.assertEqual(description, observation.description)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)

            self.assertEqual("backend/bin/run_pylint.sh", observation.origin_source_file)
            self.assertEqual(18, observation.origin_source_line_start)
            self.assertEqual(18, observation.origin_source_line_end)
            self.assertEqual(
                "https://github.com/SecObserve/SecObserve/blob/66122e6cbd0b7a7afaac29429da62bc63ee846ea/backend/bin/run_pylint.sh#L18",
                observation.origin_source_file_link,
            )

            self.assertEqual("Entry", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"Entropy": 5.152115',
                observation.unsaved_evidences[0][1],
            )
