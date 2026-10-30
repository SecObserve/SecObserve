from json import dumps
from unittest.mock import patch

from application.core.models import Product
from application.core.types import OSVLinuxDistribution
from application.scancodeio.services.results import (
    apply_osv_linux_distribution,
    get_license_components,
)
from unittests.base_test_case import BaseTestCase

# Shaped like the results of the ScanCode.io pipeline analyze_docker_image
ALPINE_PACKAGE = {
    "purl": "pkg:alpine/busybox@1.34.1-r5?arch=x86_64",
    "type": "alpine",
    "namespace": "",
    "name": "busybox",
    "version": "1.34.1-r5",
    "declared_license_expression": "gpl-2.0",
    "declared_license_expression_spdx": "GPL-2.0-only",
    "package_uid": "pkg:alpine/busybox@1.34.1-r5?arch=x86_64&uuid=1",
    "datasource_ids": ["alpine_installed_db"],
    "tag": "img-06c7c4-layer-01-40e48c",
}
APP_PACKAGE = {
    "purl": "pkg:npm/app@1.0.0",
    "type": "npm",
    "name": "app",
    "version": "1.0.0",
    "declared_license_expression": "",
    "declared_license_expression_spdx": "",
    "package_uid": "pkg:npm/app@1.0.0?uuid=2",
}
LIBRARY_PACKAGE = {
    "purl": "pkg:npm/library@2.0.0",
    "type": "npm",
    "name": "library",
    "version": "2.0.0",
    "declared_license_expression": "mit",
    "declared_license_expression_spdx": "",
    "package_uid": "pkg:npm/library@2.0.0?uuid=3",
}
TRANSITIVE_PACKAGE = {
    "purl": "pkg:npm/transitive",
    "type": "npm",
    "name": "transitive",
    "version": "",
    "declared_license_expression": "",
    "declared_license_expression_spdx": "",
    "package_uid": "pkg:npm/transitive?uuid=4",
}


def _results(packages=None, dependencies=None, images=None, tool_version="v38.2.0"):
    return {
        "headers": [
            {
                "tool_name": "scanpipe",
                "tool_version": tool_version,
                "extra_data": {"images": images or []},
            }
        ],
        "packages": packages or [],
        "dependencies": dependencies or [],
    }


def _image(identifier: str, version_id: str) -> dict:
    return {
        "image_id": "06c7c49ea0a689415b6189e13207bbca004cc6579d0d6749d33d5d0f463936a1",
        "distro": {"identifier": identifier, "version_id": version_id},
    }


class TestGetLicenseComponents(BaseTestCase):
    def test_no_packages(self):
        license_components, scanner = get_license_components(_results())

        self.assertEqual(license_components, [])
        self.assertEqual(scanner, "ScanCode.io / v38.2.0")

    def test_scanner_without_version(self):
        _, scanner = get_license_components(_results(tool_version=""))

        self.assertEqual(scanner, "ScanCode.io")

    def test_scanner_without_headers(self):
        _, scanner = get_license_components({"packages": []})

        self.assertEqual(scanner, "ScanCode.io")

    def test_packages(self):
        license_components, _ = get_license_components(
            _results(packages=[ALPINE_PACKAGE, APP_PACKAGE, LIBRARY_PACKAGE, {"name": "", "purl": "pkg:npm/x"}])
        )

        self.assertEqual(len(license_components), 3)

        alpine_component = license_components[0]
        self.assertEqual(alpine_component.component_name, "busybox")
        self.assertEqual(alpine_component.component_version, "1.34.1-r5")
        self.assertEqual(alpine_component.component_purl, "pkg:alpine/busybox@1.34.1-r5?arch=x86_64")
        self.assertEqual(alpine_component.component_dependencies, "")
        self.assertEqual(alpine_component.unsaved_declared_licenses, ["GPL-2.0-only"])
        self.assertEqual(alpine_component.unsaved_concluded_licenses, [])
        self.assertEqual(alpine_component.unsaved_evidences, [["Package", dumps(ALPINE_PACKAGE)]])

        self.assertEqual(license_components[1].component_name, "app")
        self.assertEqual(license_components[1].unsaved_declared_licenses, [])

        # Without a SPDX expression, the license expression of ScanCode is used
        self.assertEqual(license_components[2].component_name, "library")
        self.assertEqual(license_components[2].unsaved_declared_licenses, ["mit"])

    def test_dependencies(self):
        license_components, _ = get_license_components(
            _results(
                packages=[APP_PACKAGE, LIBRARY_PACKAGE, TRANSITIVE_PACKAGE],
                dependencies=[
                    {
                        "purl": "pkg:npm/library",
                        "for_package_uid": APP_PACKAGE["package_uid"],
                        "resolved_to_package_uid": LIBRARY_PACKAGE["package_uid"],
                    },
                    {
                        "purl": "pkg:npm/transitive",
                        "for_package_uid": LIBRARY_PACKAGE["package_uid"],
                        "resolved_to_package_uid": TRANSITIVE_PACKAGE["package_uid"],
                    },
                    # Dependencies declared twice, e.g. in package.json and package-lock.json, are shown once
                    {
                        "purl": "pkg:npm/transitive",
                        "for_package_uid": LIBRARY_PACKAGE["package_uid"],
                        "resolved_to_package_uid": TRANSITIVE_PACKAGE["package_uid"],
                    },
                    # Unresolved and project dependencies are no packages of the image
                    {
                        "purl": "pkg:npm/unresolved",
                        "for_package_uid": APP_PACKAGE["package_uid"],
                        "resolved_to_package_uid": None,
                    },
                    {
                        "purl": "pkg:npm/library",
                        "for_package_uid": None,
                        "resolved_to_package_uid": LIBRARY_PACKAGE["package_uid"],
                    },
                ],
            )
        )

        self.assertEqual(license_components[0].component_dependencies, "")
        self.assertEqual(license_components[1].component_dependencies, "app:1.0.0 --> library:2.0.0")
        self.assertEqual(
            license_components[2].component_dependencies,
            "app:1.0.0 --> library:2.0.0\nlibrary:2.0.0 --> transitive",
        )

    def test_dependencies_resolved_by_purl(self):
        library_package_copy = LIBRARY_PACKAGE | {"package_uid": "pkg:npm/library@2.0.0?uuid=5"}
        license_components, _ = get_license_components(
            _results(
                packages=[APP_PACKAGE, LIBRARY_PACKAGE, library_package_copy, ALPINE_PACKAGE],
                dependencies=[
                    # The same purl can belong to several packages, e.g. in different node_modules directories
                    {
                        "purl": "pkg:npm/library@2.0.0",
                        "for_package_uid": APP_PACKAGE["package_uid"],
                        "resolved_to_package_uid": None,
                    },
                    # The purls of dependencies have no qualifiers
                    {
                        "purl": "pkg:alpine/busybox@1.34.1-r5",
                        "for_package_uid": library_package_copy["package_uid"],
                        "resolved_to_package_uid": None,
                    },
                    # A package that depends on itself, e.g. in a Cargo.lock file
                    {
                        "purl": "pkg:npm/app@1.0.0",
                        "for_package_uid": APP_PACKAGE["package_uid"],
                        "resolved_to_package_uid": None,
                    },
                    # Without a version, the dependency can't be resolved
                    {
                        "purl": "pkg:npm/library",
                        "for_package_uid": APP_PACKAGE["package_uid"],
                        "resolved_to_package_uid": None,
                    },
                ],
            )
        )

        self.assertEqual(license_components[0].component_dependencies, "")
        self.assertEqual(license_components[1].component_dependencies, "app:1.0.0 --> library:2.0.0")
        self.assertEqual(license_components[2].component_dependencies, "app:1.0.0 --> library:2.0.0")
        self.assertEqual(
            license_components[3].component_dependencies,
            "app:1.0.0 --> library:2.0.0\nlibrary:2.0.0 --> busybox:1.34.1-r5",
        )


class TestApplyOSVLinuxDistribution(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product = Product(name="product")

    @patch("application.core.models.Product.save")
    def _assert_distribution(self, images, distribution, release, mock_save):
        apply_osv_linux_distribution(self.product, _results(images=images))

        self.assertEqual(self.product.osv_linux_distribution, distribution)
        self.assertEqual(self.product.osv_linux_release, release)
        if distribution:
            mock_save.assert_called_once()
        else:
            mock_save.assert_not_called()

    def test_alpine(self):
        self._assert_distribution([_image("alpine", "3.15.4")], OSVLinuxDistribution.DISTRIBUTION_ALPINE, "v3.15")

    def test_debian(self):
        self._assert_distribution([_image("debian", "11")], OSVLinuxDistribution.DISTRIBUTION_DEBIAN, "11")

    def test_ubuntu_lts(self):
        self._assert_distribution([_image("ubuntu", "22.04")], OSVLinuxDistribution.DISTRIBUTION_UBUNTU, "22.04:LTS")

    def test_ubuntu_no_lts(self):
        self._assert_distribution([_image("ubuntu", "23.10")], OSVLinuxDistribution.DISTRIBUTION_UBUNTU, "23.10")

    def test_rocky(self):
        self._assert_distribution([_image("rocky", "9.3")], OSVLinuxDistribution.DISTRIBUTION_ROCKY_LINUX, "9")

    def test_photon(self):
        self._assert_distribution([_image("photon", "5.0")], OSVLinuxDistribution.DISTRIBUTION_PHOTON_OS, "5.0")

    def test_distribution_without_release(self):
        self._assert_distribution([_image("rhel", "9.3")], OSVLinuxDistribution.DISTRIBUTION_REDHAT, "")

    def test_invalid_version(self):
        self._assert_distribution([_image("alpine", "edge")], OSVLinuxDistribution.DISTRIBUTION_ALPINE, "")

    def test_same_distribution_in_several_images(self):
        self._assert_distribution(
            [_image("debian", "11"), _image("debian", "11.2")], OSVLinuxDistribution.DISTRIBUTION_DEBIAN, "11"
        )

    def test_unsupported_distribution(self):
        self._assert_distribution([_image("centos", "7")], "", "")

    def test_different_distributions(self):
        self._assert_distribution([_image("alpine", "3.15.4"), _image("debian", "11")], "", "")

    def test_no_images(self):
        self._assert_distribution([], "", "")

    def test_no_distro(self):
        self._assert_distribution([{"image_id": "1", "distro": None}], "", "")

    @patch("application.core.models.Product.save")
    def test_unchanged(self, mock_save):
        self.product.osv_linux_distribution = OSVLinuxDistribution.DISTRIBUTION_DEBIAN
        self.product.osv_linux_release = "11"

        apply_osv_linux_distribution(self.product, _results(images=[_image("debian", "11")]))

        mock_save.assert_not_called()

    @patch("application.core.models.Product.save")
    def test_overwrites_previous_distribution(self, mock_save):
        self.product.osv_linux_distribution = OSVLinuxDistribution.DISTRIBUTION_ALPINE
        self.product.osv_linux_release = "v3.15"

        apply_osv_linux_distribution(self.product, _results(images=[_image("alpine", "3.19.1")]))

        self.assertEqual(self.product.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_ALPINE)
        self.assertEqual(self.product.osv_linux_release, "v3.19")
        mock_save.assert_called_once()
