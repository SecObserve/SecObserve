from os import path
from unittest import TestCase

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.cryptolyzer.parser import CryptoLyzerParser
from application.import_observations.services.parser_detector import detect_parser


class TestCryptolyzeParser(TestCase):
    def test_no_observations(self):
        with open(path.dirname(__file__) + "/files/no_observations.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CryptoLyzer", parser.name)
            self.assertIsInstance(parser_instance, CryptoLyzerParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("CryptoLyzer", scanner)
            self.assertEqual(0, len(observations))

    def test_multiple_observations(self):
        with open(path.dirname(__file__) + "/files/multiple_observations.json") as testfile:
            parser = CryptoLyzerParser()
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CryptoLyzer", parser.name)
            self.assertIsInstance(parser_instance, CryptoLyzerParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("CryptoLyzer", scanner)
            self.assertEqual(4, len(observations))

            observation = observations[0]
            self.assertEqual("Unrecommended TLS 1.2 cipher suites", observation.title)
            self.assertEqual(
                "**Unrecommended cipher suites:**\n* ECDHE_RSA_WITH_AES_256_GCM_SHA384\n* ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
                observation.description,
            )
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)
            self.assertEqual("https://www.example.org:443", observation.origin_endpoint_url)
            self.assertEqual("CryptoLyzer", observation.scanner)
            self.assertEqual(
                "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.pdf?__blob=publicationFile&v=5",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://docs.tlsref.org",
                observation.unsaved_references[1],
            )
            self.assertEqual("Result", observation.unsaved_evidences[0][0])
            self.assertIn(
                "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256",
                observation.unsaved_evidences[0][1],
            )

            observation = observations[1]
            self.assertEqual("Unrecommended TLS 1.3 cipher suites", observation.title)
            self.assertEqual(
                "**Unrecommended cipher suites:**\n* CHACHA20_POLY1305_SHA256",
                observation.description,
            )
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)
            self.assertEqual("https://www.example.org:443", observation.origin_endpoint_url)
            self.assertEqual("CryptoLyzer", observation.scanner)
            self.assertEqual(
                "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.pdf?__blob=publicationFile&v=5",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://docs.tlsref.org",
                observation.unsaved_references[1],
            )
            self.assertEqual("Result", observation.unsaved_evidences[0][0])
            self.assertIn("TLS_AES_128_GCM_SHA256", observation.unsaved_evidences[0][1])

            observation = observations[2]
            self.assertEqual("Unrecommended elliptic curves", observation.title)
            self.assertEqual(
                "**Unrecommended elliptic curves:**\n* X448",
                observation.description,
            )
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)
            self.assertEqual("https://www.example.org:443", observation.origin_endpoint_url)
            self.assertEqual("CryptoLyzer", observation.scanner)
            self.assertEqual(
                "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.pdf?__blob=publicationFile&v=5",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://docs.tlsref.org",
                observation.unsaved_references[1],
            )
            self.assertEqual("Result", observation.unsaved_evidences[0][0])
            self.assertIn("X25519", observation.unsaved_evidences[0][1])

            observation = observations[3]
            self.assertEqual("Unrecommended signature algorithms", observation.title)
            self.assertEqual(
                "**Unrecommended signature algorithms:**\n* RSA_SHA1\n* RSA_SHA224",
                observation.description,
            )
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)
            self.assertEqual("https://www.example.org:443", observation.origin_endpoint_url)
            self.assertEqual("CryptoLyzer", observation.scanner)
            self.assertEqual(
                "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.pdf?__blob=publicationFile&v=5",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://docs.tlsref.org",
                observation.unsaved_references[1],
            )
            self.assertEqual("Result", observation.unsaved_evidences[0][0])
            self.assertIn("RSA_SHA224", observation.unsaved_evidences[0][1])

    def test_weak_tls(self):
        with open(path.dirname(__file__) + "/files/tls10.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CryptoLyzer", parser.name)
            self.assertIsInstance(parser_instance, CryptoLyzerParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("CryptoLyzer", scanner)
            self.assertEqual(3, len(observations))

            observation = observations[0]
            self.assertEqual("Weak protocols detected", observation.title)
            self.assertEqual(
                "**Weak protocols:**\n* tls1\n* tls1_1",
                observation.description,
            )
            self.assertEqual(Severity.SEVERITY_HIGH, observation.parser_severity)
            self.assertEqual("https://tls-v1-0.badssl.com:443", observation.origin_endpoint_url)
            self.assertEqual("CryptoLyzer", observation.scanner)
            self.assertEqual(
                "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.pdf?__blob=publicationFile&v=5",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://docs.tlsref.org",
                observation.unsaved_references[1],
            )
            self.assertEqual("Result", observation.unsaved_evidences[0][0])
            self.assertIn("tls1_1", observation.unsaved_evidences[0][1])
