from unittest import TestCase

from application.core.models import Observation
from application.import_observations.management.commands.register_parsers import Command
from application.import_observations.models import Api_Configuration, Parser


class TestRegisterParsers(TestCase):

    def setUp(self):
        Api_Configuration.objects.all().delete()
        Observation.objects.all().delete()
        Parser.objects.all().delete()

    def test_register_parsers(self):
        command = Command()
        command.handle()

        parsers = Parser.objects.all().order_by("name")
        self.assertEqual(16, len(parsers))

        parser = parsers[0]
        self.assertEqual("Azure Defender", parser.name)
        self.assertEqual("Infrastructure", parser.type)
        self.assertEqual("File", parser.source)
        self.assertEqual("azure_defender", parser.module_name)
        self.assertEqual("AzureDefenderParser", parser.class_name)

        parser = parsers[1]
        self.assertEqual("CryptoLyzer", parser.name)
        self.assertEqual("DAST", parser.type)
        self.assertEqual("File", parser.source)
        self.assertEqual("cryptolyzer", parser.module_name)
        self.assertEqual("CryptoLyzerParser", parser.class_name)

        parser = parsers[7]
        self.assertEqual("Manual", parser.name)
        self.assertEqual("Manual", parser.type)
        self.assertEqual("Manual", parser.source)
        self.assertEqual("", parser.module_name)
        self.assertEqual("", parser.class_name)

        parser = parsers[14]
        self.assertEqual("Trivy Operator Prometheus", parser.name)
        self.assertEqual("Other", parser.type)
        self.assertEqual("API", parser.source)
        self.assertEqual("trivy_operator_prometheus", parser.module_name)
        self.assertEqual("TrivyOperatorPrometheus", parser.class_name)
