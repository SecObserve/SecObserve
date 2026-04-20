from json import load
from os import path
from unittest import TestCase

from rest_framework.exceptions import ValidationError

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.kubescape.parser import KubescapeParser
from application.import_observations.services.parser_detector import detect_parser


class TestKubescapeParser(TestCase):
    def test_kubescape(self):
        with open(path.dirname(__file__) + "/files/kubescape.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("Kubescape", parser.name)
            self.assertIsInstance(parser_instance, KubescapeParser)

            observations, scanner = parser_instance.get_observations(data, None, None)

            self.assertEqual("Kubescape / v3.0.48", scanner)
            self.assertEqual(11, len(observations))

            observation = observations[0]
            self.assertEqual("C-0015 / List Kubernetes secrets", observation.title)
            self.assertEqual(Severity.SEVERITY_HIGH, observation.parser_severity)

            self.assertEqual("kind-quickstart", observation.origin_kubernetes_cluster)
            self.assertEqual("operators", observation.origin_kubernetes_namespace)
            self.assertEqual("ServiceAccount", observation.origin_kubernetes_resource_type)
            self.assertEqual("tool1-operator-serviceaccount", observation.origin_kubernetes_resource_name)

            self.assertEqual("https://kubescape.io/docs/controls/c-0015", observation.unsaved_references[0])

            self.assertEqual("Control", observation.unsaved_evidences[0][0])
            self.assertIn(
                "relatedObjects[1].rules[2].resources[2]",
                observation.unsaved_evidences[0][1],
            )
            self.assertEqual("Resource", observation.unsaved_evidences[1][0])
            self.assertIn(
                "82d256bb-2bef-4c73-a7e0-fe8d8d9ed178",
                observation.unsaved_evidences[1][1],
            )

            observation = observations[10]
            self.assertEqual("C-0055 / Linux hardening", observation.title)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)

            self.assertEqual("kind-quickstart", observation.origin_kubernetes_cluster)
            self.assertEqual("operators", observation.origin_kubernetes_namespace)
            self.assertEqual("Deployment", observation.origin_kubernetes_resource_type)
            self.assertEqual("tool2-operator-deployment", observation.origin_kubernetes_resource_name)
