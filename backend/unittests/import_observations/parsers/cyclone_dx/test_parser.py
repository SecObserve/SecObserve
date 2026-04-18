from os import path
from unittest import TestCase

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.cyclone_dx.parser import CycloneDXParser
from application.import_observations.services.parser_detector import detect_parser


class TestCycloneDXParser(TestCase):
    def test_grype_no_bom_link(self):
        with open(path.dirname(__file__) + "/files/grype.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CycloneDX", parser.name)
            self.assertIsInstance(parser_instance, CycloneDXParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("grype / 0.59.1", scanner)
            self.assertEqual(8, len(observations))

            observation = observations[0]
            self.assertEqual("grype / 0.59.1", observation.scanner)
            self.assertEqual(
                "CVE-2007-4559",
                observation.title,
            )
            description = """Directory traversal vulnerability in the (1) extract and (2) extractall functions in the tarfile module in Python allows user-assisted remote attackers to overwrite arbitrary files via a .. (dot dot) sequence in filenames in a TAR archive, a related issue to CVE-2001-1267."""
            self.assertEqual(description, observation.description)
            self.assertEqual("CVE-2007-4559", observation.vulnerability_id)
            self.assertEqual(Severity.SEVERITY_MEDIUM, observation.parser_severity)
            self.assertEqual("python", observation.origin_component_name)
            self.assertEqual("3.11.3", observation.origin_component_version)
            self.assertEqual("Application", observation.origin_component_type)
            self.assertEqual("pkg:generic/python@3.11.3", observation.origin_component_purl)
            self.assertEqual(
                "cpe:2.3:a:python_software_foundation:python:3.11.3:*:*:*:*:*:*:*",
                observation.origin_component_cpe,
            )
            self.assertEqual("", observation.origin_component_cyclonedx_bom_link)
            self.assertEqual("example/example:dev", observation.origin_docker_image_name)
            self.assertEqual("", observation.origin_docker_image_tag)
            self.assertEqual(
                "sha256:88901af20b50287be153ec4f20ed78f947eb5fa0d0a52432ced6e261b66b6cbc",
                observation.origin_docker_image_digest,
            )
            self.assertEqual(
                "http://mail.python.org/pipermail/python-dev/2007-August/074290.html",
                observation.unsaved_references[0],
            )
            self.assertEqual("Vulnerability", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"ref": "pkg:generic/python@3.11.3?package-id=6116cb95a76157bb"',
                observation.unsaved_evidences[0][1],
            )
            self.assertEqual("Component", observation.unsaved_evidences[1][0])
            self.assertIn(
                '"bom-ref": "pkg:generic/python@3.11.3?package-id=6116cb95a76157bb"',
                observation.unsaved_evidences[1][1],
            )

            observation = observations[2]
            self.assertEqual("grype / 0.59.1", observation.scanner)
            self.assertEqual(
                "CVE-2022-47015",
                observation.title,
            )
            description = """MariaDB Server before 10.3.34 thru 10.9.3 is vulnerable to Denial of Service. It is possible for function spider_db_mbase::print_warnings to dereference a null pointer."""
            self.assertEqual(description, observation.description)
            self.assertEqual("CVE-2022-47015", observation.vulnerability_id)
            self.assertEqual("", observation.parser_severity)
            self.assertEqual(6.5, observation.cvss3_score)
            self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
            self.assertEqual("mariadb-client", observation.origin_component_name)
            self.assertEqual("10.6.12-r0", observation.origin_component_version)
            self.assertEqual("Library", observation.origin_component_type)
            self.assertEqual(
                "pkg:apk/alpine/mariadb-client@10.6.12-r0?arch=x86_64&upstream=mariadb&distro=alpine-3.17.3",
                observation.origin_component_purl,
            )
            self.assertEqual(
                "cpe:2.3:a:mariadb-client:mariadb-client:10.6.12-r0:*:*:*:*:*:*:*",
                observation.origin_component_cpe,
            )
            self.assertEqual("example/example:dev", observation.origin_docker_image_name)
            self.assertEqual("", observation.origin_docker_image_tag)
            self.assertEqual(
                "sha256:88901af20b50287be153ec4f20ed78f947eb5fa0d0a52432ced6e261b66b6cbc",
                observation.origin_docker_image_digest,
            )
            self.assertEqual(
                "https://github.com/MariaDB/server/commit/be0a46b3d52b58956fd0d47d040b9f4514406954",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://security.netapp.com/advisory/ntap-20230309-0009/",
                observation.unsaved_references[1],
            )
            self.assertEqual("Vulnerability", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"ref": "pkg:apk/alpine/mariadb-client@10.6.12-r0?arch=x86_64&upstream=mariadb&distro=alpine-3.17.3&package-id=785616ef5bcd9445"',
                observation.unsaved_evidences[0][1],
            )
            self.assertEqual("Component", observation.unsaved_evidences[1][0])
            self.assertIn(
                '"bom-ref": "pkg:apk/alpine/mariadb-client@10.6.12-r0?arch=x86_64&upstream=mariadb&distro=alpine-3.17.3&package-id=785616ef5bcd9445"',
                observation.unsaved_evidences[1][1],
            )

    def test_grype_component_version(self):
        with open(path.dirname(__file__) + "/files/grype_2.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CycloneDX", parser.name)
            self.assertIsInstance(parser_instance, CycloneDXParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("grype / 0.65.1", scanner)
            self.assertEqual(1, len(observations))

            observation = observations[0]
            self.assertEqual("CVE-2018-20225", observation.vulnerability_id)
            self.assertEqual("grype / 0.65.1", observation.scanner)
            self.assertEqual("example/example-backend", observation.origin_docker_image_name)
            self.assertEqual("dev", observation.origin_docker_image_tag)
            self.assertEqual("", observation.origin_docker_image_digest)

    def test_grype_tools_components(self):
        with open(path.dirname(__file__) + "/files/grype_3.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CycloneDX", parser.name)
            self.assertIsInstance(parser_instance, CycloneDXParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("grype / 0.73.5", scanner)
            self.assertEqual(1, len(observations))

            observation = observations[0]
            self.assertEqual("CVE-2023-42363", observation.vulnerability_id)
            self.assertEqual("grype / 0.73.5", observation.scanner)
            self.assertEqual("example/example-backend", observation.origin_docker_image_name)
            self.assertEqual("dev", observation.origin_docker_image_tag)
            self.assertEqual("", observation.origin_docker_image_digest)

    def test_trivy_observations(self):
        self.maxDiff = None

        with open(path.dirname(__file__) + "/files/trivy.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CycloneDX", parser.name)
            self.assertIsInstance(parser_instance, CycloneDXParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("trivy / 0.38.3", scanner)
            self.assertEqual(2, len(observations))

            observation = observations[0]
            self.assertEqual("trivy / 0.38.3", observation.scanner)
            self.assertEqual("CVE-2023-29469", observation.title)
            description = """No description is available for this CVE."""
            self.assertEqual(description, observation.description)
            self.assertEqual("CVE-2023-29469", observation.vulnerability_id)
            self.assertEqual("GHSA-35m5-8cvj-8783, alias 2", observation.vulnerability_id_aliases)
            self.assertEqual("", observation.parser_severity)
            self.assertEqual(5.9, observation.cvss3_score)
            self.assertEqual("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
            self.assertEqual("libxml2", observation.origin_component_name)
            self.assertEqual("2.10.3-r1", observation.origin_component_version)
            self.assertEqual("Library", observation.origin_component_type)
            self.assertEqual(
                "pkg:apk/alpine/libxml2@2.10.3-r1?distro=3.17.3",
                observation.origin_component_purl,
            )
            self.assertEqual(
                "urn:cdx:fa9f9148-2935-422a-b058-20afa8cafa82/99#pkg:apk/alpine/libxml2@2.10.3-r1?distro=3.17.3",
                observation.origin_component_cyclonedx_bom_link,
            )
            self.assertEqual("example/example-frontend:dev", observation.origin_docker_image_name)
            self.assertEqual("", observation.origin_docker_image_tag)
            self.assertEqual("", observation.origin_docker_image_digest)
            expected_dependencies = """alpine:3.17.3 --> libxml2:2.10.3-r1
example/example-frontend:dev --> alpine:3.17.3"""
            self.assertEqual(expected_dependencies, observation.origin_component_dependencies)
            self.assertEqual(
                "https://access.redhat.com/security/cve/CVE-2023-29469",
                observation.unsaved_references[0],
            )
            self.assertEqual("Vulnerability", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"ref": "pkg:apk/alpine/libxml2@2.10.3-r1?distro=3.17.3"',
                observation.unsaved_evidences[0][1],
            )
            self.assertEqual("Component", observation.unsaved_evidences[1][0])
            self.assertIn(
                '"bom-ref": "pkg:apk/alpine/libxml2@2.10.3-r1?distro=3.17.3"',
                observation.unsaved_evidences[1][1],
            )

            observation = observations[1]
            self.assertEqual("CVE-2023-28484", observation.title)
            expected_dependencies = """alpine:3.17.3 --> busybox:1.35.0-r29
alpine:3.17.3 --> geoip:1.6.12-r3
alpine:3.17.3 --> icu-data-en:72.1-r1
alpine:3.17.3 --> icu-libs:72.1-r1
busybox:1.35.0-r29 --> icu-libs:72.1-r1
example/example-frontend:dev --> alpine:3.17.3
geoip:1.6.12-r3 --> icu-data-en:72.1-r1
icu-data-en:72.1-r1 --> geoip:1.6.12-r3
icu-data-en:72.1-r1 --> icu-libs:72.1-r1"""
            self.assertEqual(
                expected_dependencies,
                observation.origin_component_dependencies,
            )
            self.assertEqual("", observation.parser_severity)
            self.assertEqual(5.9, observation.cvss3_score)
            self.assertEqual("CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
            self.assertEqual(8.8, observation.cvss4_score)
            self.assertEqual(
                "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:L/VA:L/SC:L/SI:L/SA:N",
                observation.cvss4_vector,
            )

    def test_trivy_license_components(self):
        self.maxDiff = None

        with open(path.dirname(__file__) + "/files/trivy.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("CycloneDX", parser.name)
            self.assertIsInstance(parser_instance, CycloneDXParser)

            license_components, scanner = parser_instance.get_license_components(data)

            self.assertEqual("trivy / 0.38.3", scanner)
            self.assertEqual(87, len(license_components))

            license_component = license_components[10]
            self.assertEqual("c-ares", license_component.component_name)
            self.assertEqual("1.18.1-r1", license_component.component_version)
            self.assertEqual("Library", license_component.component_type)
            self.assertEqual("pkg:apk/alpine/c-ares@1.18.1-r1?distro=3.17.3", license_component.component_purl)
            self.assertEqual("", license_component.component_cpe)
            self.assertEqual(
                "urn:cdx:fa9f9148-2935-422a-b058-20afa8cafa82/99#pkg:apk/alpine/c-ares@1.18.1-r1?distro=3.17.3",
                license_component.component_cyclonedx_bom_link,
            )
            dependencies = """alpine:3.17.3 --> c-ares:1.18.1-r1
example/example-frontend:dev --> alpine:3.17.3"""
            self.assertEqual(dependencies, license_component.component_dependencies)
            self.assertEqual(["MIT"], license_component.unsaved_declared_licenses)
            self.assertEqual("Component", license_component.unsaved_evidences[0][0])
            self.assertIn(
                '"bom-ref": "pkg:apk/alpine/c-ares@1.18.1-r1?distro=3.17.3"',
                license_component.unsaved_evidences[0][1],
            )

            license_component = license_components[11]
            self.assertEqual("ca-certificates", license_component.component_name)
            self.assertEqual("20220614-r4", license_component.component_version)
            self.assertEqual(["MPL-2.0", "MIT"], license_component.unsaved_declared_licenses)

            license_component = license_components[12]
            self.assertEqual("ca-certificates-bundle", license_component.component_name)
            self.assertEqual("20220614-r4", license_component.component_version)
            self.assertEqual(["MPL-2.0", "MIT"], license_component.unsaved_concluded_licenses)
