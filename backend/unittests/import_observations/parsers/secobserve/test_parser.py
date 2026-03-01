from os import path
from unittest import TestCase

from application.core.models import Product
from application.import_observations.parsers.secobserve.parser import SecObserveParser
from application.import_observations.services.parser_detector import detect_parser


class TestSecObserveParser(TestCase):
    def test_no_observation(self):
        with open(path.dirname(__file__) + "/files/no_observation.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("SecObserve", parser.name)
            self.assertIsInstance(parser_instance, SecObserveParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("SecObserve", scanner)
            self.assertEqual(0, len(observations))

    def test_multiple_observations(self):
        with open(path.dirname(__file__) + "/files/multiple_observations.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("SecObserve", parser.name)
            self.assertIsInstance(parser_instance, SecObserveParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("scanner_1", scanner)
            self.assertEqual(2, len(observations))

            observation = observations[0]
            self.assertEqual("title_1", observation.title)
            self.assertEqual("description_1", observation.description)
            self.assertEqual("recommendation_1", observation.recommendation)
            self.assertEqual("Critical", observation.parser_severity)
            self.assertEqual("scanner_observation_id_1", observation.scanner_observation_id)
            self.assertEqual("vulnerability_id_1", observation.vulnerability_id)
            self.assertEqual("origin_component_name_1", observation.origin_component_name)
            self.assertEqual("origin_component_version_1", observation.origin_component_version)
            self.assertEqual(
                "origin_component_name_version_1",
                observation.origin_component_name_version,
            )
            self.assertEqual("origin_component_purl_1", observation.origin_component_purl)
            self.assertEqual("origin_component_cpe_1", observation.origin_component_cpe)
            self.assertEqual("origin_docker_image_name_1", observation.origin_docker_image_name)
            self.assertEqual("origin_docker_image_tag_1", observation.origin_docker_image_tag)
            self.assertEqual(
                "origin_docker_image_name_tag_1",
                observation.origin_docker_image_name_tag,
            )
            self.assertEqual("origin_endpoint_url_1", observation.origin_endpoint_url)
            self.assertEqual("origin_source_file_1", observation.origin_source_file)
            self.assertEqual(10, observation.origin_source_line_start)
            self.assertEqual(11, observation.origin_source_line_end)
            self.assertEqual(1.1, observation.cvss3_score)
            self.assertEqual("cvss3_vector_1", observation.cvss3_vector)
            self.assertEqual(1, observation.cwe)
            self.assertEqual("scanner_1", observation.scanner)

            observation = observations[1]
            self.assertEqual("title_2", observation.title)
            self.assertEqual(1, len(observation.unsaved_references))
            self.assertEqual("https://example.com", observation.unsaved_references[0])
