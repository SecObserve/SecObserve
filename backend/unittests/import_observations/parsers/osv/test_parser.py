from datetime import datetime, timezone
from unittest.mock import patch

from django.core.management import call_command
from packageurl import PackageURL

from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
    OSVParser,
)
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase


class TestOSVParser(BaseTestCase):
    def test_no_observations(self):
        parser = OSVParser()
        observations, scanner = parser.get_observations([], self.product_1, self.branch_1)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(observations, [])

    def test_java_and_python_open(self):
        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_java_python.json",
            ],
        )

        license_component_java = License_Component(
            product=self.product_1,
            branch=self.branch_1,
            component_name="json",
            component_version="20190722",
            component_name_version="json:20190722",
            component_purl="pkg:maven/org.json/json@20190722?type=jar",
            component_purl_type="maven",
            component_cpe="cpe:/a:org.json:json:20190722",
            component_cyclonedx_bom_link="urn:cdx:a/1#b",
            component_dependencies="json_dependencies",
        )

        license_component_python = License_Component(
            product=self.product_1,
            branch=self.branch_1,
            component_name="Django",
            component_version="5.1.2",
            component_name_version="Django:5.1.2",
            component_purl="pkg:pypi/django@5.1.2",
            component_purl_type="pypi",
            component_dependencies="django_dependencies",
        )

        osv_components = [
            OSV_Component(
                license_component=license_component_java,
                vulnerabilities={
                    OSV_Vulnerability(
                        id="GHSA-3vqj-43w4-2q58",
                        modified=datetime(2024, 8, 7, 20, 1, 58, 452618, timezone.utc),
                    ),
                    OSV_Vulnerability(
                        id="GHSA-4jq9-2xhw-jpx7",
                        modified=datetime(2024, 10, 30, 19, 23, 43, 662562, timezone.utc),
                    ),
                },
            ),
            OSV_Component(
                license_component=license_component_python,
                vulnerabilities={
                    OSV_Vulnerability(
                        id="GHSA-m9g8-fxxm-xg86",
                        modified=datetime(2024, 12, 20, 20, 37, 27, 0, timezone.utc),
                    ),
                },
            ),
        ]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, self.branch_1)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(len(observations), 3)

        observation = observations[0]
        self.assertEqual("CVE-2022-45688", observation.title)
        description = """json stack overflow vulnerability

A stack overflow in the XML.toJSONObject component of hutool-json v5.8.10 and org.json:json before version 20230227 allows attackers to cause a Denial of Service (DoS) via crafted JSON or XML data.

**Confidence: High** (Component found in affected versions)"""
        self.assertEqual(description, observation.description)
        self.assertEqual("", observation.recommendation)
        self.assertEqual("CVE-2022-45688", observation.vulnerability_id)
        self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
        self.assertEqual("", observation.cvss4_vector)
        self.assertEqual("GHSA-3vqj-43w4-2q58", observation.vulnerability_id_aliases)
        self.assertEqual("json", observation.origin_component_name)
        self.assertEqual("20190722", observation.origin_component_version)
        self.assertEqual(
            "pkg:maven/org.json/json@20190722?type=jar",
            observation.origin_component_purl,
        )
        self.assertEqual("cpe:/a:org.json:json:20190722", observation.origin_component_cpe)
        self.assertEqual("urn:cdx:a/1#b", observation.origin_component_cyclonedx_bom_link)
        self.assertEqual("json_dependencies", observation.origin_component_dependencies)

        unsaved_references = observation.unsaved_references
        self.assertEqual(6, len(unsaved_references))
        self.assertEqual("https://nvd.nist.gov/vuln/detail/CVE-2022-45688", unsaved_references[0])

        self.assertEqual("OSV Vulnerability", observation.unsaved_evidences[0][0])
        self.assertIn("CWE-787", observation.unsaved_evidences[0][1])

        observation = observations[1]
        self.assertEqual("CVE-2023-5072", observation.title)

        observation = observations[2]
        self.assertEqual("CVE-2024-53908", observation.title)
        self.assertEqual("Update to version 5.1.4", observation.recommendation)
        self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", observation.cvss3_vector)
        self.assertEqual(
            "CVSS:4.0/AV:N/AC:L/AT:P/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N/E:U",
            observation.cvss4_vector,
        )

    def test_python_fixed(self):
        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_java_python.json",
            ],
        )

        license_component_python = License_Component(
            product=self.product_1,
            branch=self.branch_1,
            component_name="Django",
            component_version="5.1.6",
            component_name_version="Django:5.1.6",
            component_purl="pkg:pypi/django@5.1.6",
            component_purl_type="pypi",
            component_dependencies="django_dependencies",
        )

        osv_components = [
            OSV_Component(
                license_component=license_component_python,
                vulnerabilities={
                    OSV_Vulnerability(
                        id="GHSA-m9g8-fxxm-xg86",
                        modified=datetime(2024, 12, 20, 20, 37, 27, 0, timezone.utc),
                    ),
                },
            ),
        ]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, self.branch_1)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(len(observations), 0)

    @patch("application.import_observations.parsers.osv.parser.OSVParser._get_linux_package_osv_ecosystem")
    def test_linux_no_distribution(self, mock_get_linux_package_osv_ecosystem):
        mock_get_linux_package_osv_ecosystem.side_effect = self._side_effect_func

        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_linux.json",
            ],
        )

        self.product_1.osv_linux_distribution = ""
        self.product_1.osv_linux_release = ""
        osv_components = [self._get_osv_component_git(), self._get_osv_component_vim()]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, None)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(len(observations), 0)

    @patch("application.import_observations.parsers.osv.parser.OSVParser._get_linux_package_osv_ecosystem")
    def test_linux_product_distribution(self, mock_get_linux_package_osv_ecosystem):
        mock_get_linux_package_osv_ecosystem.side_effect = self._side_effect_func

        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_linux.json",
            ],
        )

        self.product_1.osv_linux_distribution = "Debian"
        self.product_1.osv_linux_release = "12"
        osv_components = [self._get_osv_component_git(), self._get_osv_component_vim()]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, None)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)

        mock_get_linux_package_osv_ecosystem.assert_called_with(
            PackageURL.from_string("pkg:deb/debian/vim@9.0.1378-2?arch=amd64&distro=debian-12.5&epoch=2"),
            "Debian:12",
        )

        self.assertEqual(len(observations), 1)

        observation = observations[0]
        self.assertEqual("CVE-2017-6349", observation.title)
        description = """An integer overflow at a u_read_undo memory allocation site would occur for vim before patch 8.0.0377, if it does not properly validate values for tree length when reading a corrupted undo file, which may lead to resultant buffer overflows.

**Confidence: Low** (Events could not be evaluated)

**Events:**

* ECOSYSTEM: Introduced: 0 - Fixed: 2:8.0.0197-3"""
        self.assertEqual(description, observation.description)

    def test_linux_branch_distribution(self):
        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_linux.json",
            ],
        )

        self.product_1.osv_linux_distribution = ""
        self.product_1.osv_linux_release = ""
        self.branch_1.osv_linux_distribution = "Debian"
        self.branch_1.osv_linux_release = "12"
        osv_components = [self._get_osv_component_git(), self._get_osv_component_vim()]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, self.branch_1)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(len(observations), 1)

        observation = observations[0]
        self.assertEqual("CVE-2017-6349", observation.title)
        description = """An integer overflow at a u_read_undo memory allocation site would occur for vim before patch 8.0.0377, if it does not properly validate values for tree length when reading a corrupted undo file, which may lead to resultant buffer overflows.

**Confidence: Low** (Events could not be evaluated)

**Events:**

* ECOSYSTEM: Introduced: 0 - Fixed: 2:8.0.0197-3"""
        self.assertEqual(description, observation.description)

    def test_linux_rpm(self):
        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_rpm.json",
            ],
        )

        self.product_1.osv_linux_distribution = ""
        self.product_1.osv_linux_release = ""
        self.branch_1.osv_linux_distribution = "Red Hat"
        self.branch_1.osv_linux_release = "enterprise_linux:9::appstream"
        osv_components = [self._get_osv_component_rpm()]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, self.branch_1)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(len(observations), 1)

        observation = observations[0]
        self.assertEqual("RHSA-2023:6738", observation.title)
        description = """Red Hat Security Advisory: java-21-openjdk security and bug fix update

**Confidence: High** (Component found in affected ranges)"""
        self.assertEqual(description, observation.description)

    def test_linux_rpm_ecosystem_not_found(self):
        call_command(
            "loaddata",
            [
                "unittests/import_observations/parsers/osv/files/fixtures_osv_cache_rpm_ecosystem.json",
            ],
        )

        self.product_1.osv_linux_distribution = ""
        self.product_1.osv_linux_release = ""
        self.branch_1.osv_linux_distribution = "Red Hat"
        self.branch_1.osv_linux_release = "enterprise_linux:9::appstream"
        osv_components = [self._get_osv_component_rpm_openssl()]

        parser = OSVParser()
        observations, scanner = parser.get_observations(osv_components, self.product_1, self.branch_1)

        self.assertEqual("OSV (Open Source Vulnerabilities)", scanner)
        self.assertEqual(len(observations), 0)

    def test_get_linux_package_osv_ecosystem_already_set(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string(
                "pkg:apk/alpine/musl@1.2.5-r1?arch=x86_64&distro=alpine-3.20.6&distro_name=alpine-3.20"
            ),
            "Debian:12",
        )
        self.assertEqual("Debian:12", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_alpine_1(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string(
                "pkg:apk/alpine/musl@1.2.5-r1?arch=x86_64&distro=alpine-3.20.6&distro_name=alpine-3.20"
            ),
            None,
        )
        self.assertEqual("Alpine:v3.20", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_alpine_2(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:apk/alpine/busybox-binsh@1.44.1-r12?arch=x86_64&distro=3.21.3"),
            None,
        )
        self.assertEqual("Alpine:v3.21", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_debian_1(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:deb/debian/libtasn1-6@4.16.0-2%2Bdeb11u2?arch=amd64&distro=debian-11"),
            None,
        )
        self.assertEqual("Debian:11", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_debian_2(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:deb/debian/coreutils@8.32-4%2Bb1?arch=amd64&distro=debian-11.11"),
            None,
        )
        self.assertEqual("Debian:11", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_chainguard(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:apk/chainguard/nri-kafka@3.10.2-r0?arch=x86_64&distro=20230201"),
            None,
        )
        self.assertEqual("Chainguard", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_wolfi(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:apk/wolfi/nri-kafka@3.10.2-r0?arch=x86_64&distro=20230201"),
            None,
        )
        self.assertEqual("Wolfi", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_ubuntu_21_04(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:deb/ubuntu/zlib1g@1.2.11.dfsg-2ubuntu9?arch=amd64&distro=ubuntu-21.04&epoch=1"),
            None,
        )
        self.assertEqual("Ubuntu:21.04", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_ubuntu_22_10(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:deb/ubuntu/zlib1g@1.2.11.dfsg-2ubuntu9?arch=amd64&distro=ubuntu-22.10&epoch=1"),
            None,
        )
        self.assertEqual("Ubuntu:22.10", package_osv_ecosystem)

    def test_get_linux_package_osv_ecosystem_ubuntu_lts(self):
        parser = OSVParser()
        package_osv_ecosystem = parser._get_linux_package_osv_ecosystem(
            PackageURL.from_string("pkg:deb/ubuntu/zlib1g@1.2.11.dfsg-2ubuntu9?arch=amd64&distro=ubuntu-22.04&epoch=1"),
            None,
        )
        self.assertEqual("Ubuntu:22.04:LTS", package_osv_ecosystem)

    def _side_effect_func(self, parsed_purl, package_osv_ecosystem):
        return package_osv_ecosystem

    def _get_osv_component_git(self):
        return OSV_Component(
            license_component=License_Component(
                product=self.product_1,
                branch=self.branch_1,
                component_name="git",
                component_version="1:2.39.5-0+deb12u1",
                component_name_version="git:1:2.39.5-0+deb12u1",
                component_purl="pkg:deb/debian/git@1:2.39.5-0%2Bdeb12u1?arch=amd64&distro=debian-12",
                component_purl_type="deb",
                component_dependencies="git_dependencies",
            ),
            vulnerabilities={
                OSV_Vulnerability(
                    id="CVE-2024-32002",
                    modified=datetime(2024, 8, 7, 20, 1, 58, 452618, timezone.utc),
                ),
            },
        )

    def _get_osv_component_vim(self):
        return OSV_Component(
            license_component=License_Component(
                product=self.product_1,
                branch=self.branch_1,
                component_name="vim",
                component_version="2:9.0.1378-2",
                component_name_version="vim:2:9.0.1378-2",
                component_purl="pkg:deb/debian/vim@9.0.1378-2?arch=amd64&distro=debian-12.5&epoch=2",
                component_purl_type="deb",
                component_dependencies="vim_dependencies",
            ),
            vulnerabilities={
                OSV_Vulnerability(
                    id="CVE-2017-6349",
                    modified=datetime(2024, 8, 7, 20, 1, 58, 452618, timezone.utc),
                ),
            },
        )

    def _get_osv_component_rpm(self):
        return OSV_Component(
            license_component=License_Component(
                product=self.product_1,
                branch=self.branch_1,
                component_name="java-21-openjdk-devel",
                component_version="21.0.7.0.6-1.el9",
                component_name_version="java-21-openjdk-devel:21.0.7.0.6-1.el9",
                component_purl="pkg:rpm/redhat/java-21-openjdk-devel@21.0.7.0.6-1.el9",
                component_purl_type="rpm",
                component_dependencies="",
            ),
            vulnerabilities={
                OSV_Vulnerability(
                    id="RHSA-2023:6738",
                    modified=datetime(2024, 8, 7, 20, 1, 58, 452618, timezone.utc),
                ),
            },
        )

    def _get_osv_component_rpm_openssl(self):
        return OSV_Component(
            license_component=License_Component(
                product=self.product_1,
                branch=self.branch_1,
                component_name="openssl-libs",
                component_version="1:3.2.2-6.el9_5.1",
                component_name_version="openssl-libs:1:3.2.2-6.el9_5.1",
                component_purl="pkg:rpm/redhat/openssl-libs@3.2.2-6.el9_5.1",
                component_purl_type="rpm",
                component_dependencies="",
            ),
            vulnerabilities={
                OSV_Vulnerability(
                    id="RHSA-2015:1115",
                    modified=datetime(2025, 6, 16, 6, 2, 31, 452618, timezone.utc),
                ),
            },
        )
