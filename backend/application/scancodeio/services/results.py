from json import dumps
from typing import Any, Callable, Optional

from application.core.models import Product
from application.core.types import OSVLinuxDistribution
from application.licenses.models import License_Component


def get_license_components(results: dict[str, Any]) -> tuple[list[License_Component], str]:
    packages: dict[str, dict[str, Any]] = {}
    for package in results.get("packages", []):
        if package.get("name"):
            packages[package.get("package_uid") or package.get("purl") or package["name"]] = package

    dependencies = _get_dependencies(results, packages)

    license_components = []
    for package_uid, package in packages.items():
        license_component = License_Component(
            component_name=package["name"],
            component_version=package.get("version") or "",
            component_purl=package.get("purl") or "",
            component_dependencies=_get_component_dependencies(package_uid, packages, dependencies),
        )

        declared_license = package.get("declared_license_expression_spdx") or package.get("declared_license_expression")
        if declared_license:
            license_component.unsaved_declared_licenses = [declared_license]

        license_component.unsaved_evidences.append(["Package", dumps(package)])
        license_components.append(license_component)

    return license_components, _get_scanner(results)


def apply_osv_linux_distribution(product: Product, results: dict[str, Any]) -> None:
    """
    Sets the Linux distribution and release of the analyzed Docker image, which are needed by the
    OSV scan to find vulnerabilities of the operating system packages. The purls of ScanCode.io
    don't contain a distro qualifier, so the OSV scan can't get them from the components.
    """
    distributions = {_get_osv_linux_distribution(image.get("distro") or {}) for image in _get_images(results)}

    # With several images of different distributions, none of them is valid for the whole product
    if len(distributions) != 1:
        return

    osv_linux_distribution, osv_linux_release = distributions.pop()
    if not osv_linux_distribution:
        return

    if product.osv_linux_distribution != osv_linux_distribution or product.osv_linux_release != osv_linux_release:
        product.osv_linux_distribution = osv_linux_distribution
        product.osv_linux_release = osv_linux_release
        product.save()


def _get_headers(results: dict[str, Any]) -> dict[str, Any]:
    headers = results.get("headers")
    if isinstance(headers, list) and headers and isinstance(headers[0], dict):
        return headers[0]
    return {}


def _get_scanner(results: dict[str, Any]) -> str:
    tool_version = _get_headers(results).get("tool_version")
    if tool_version:
        return f"ScanCode.io / {tool_version}"
    return "ScanCode.io"


def _get_images(results: dict[str, Any]) -> list[dict[str, Any]]:
    extra_data = _get_headers(results).get("extra_data") or {}
    images = extra_data.get("images") if isinstance(extra_data, dict) else None
    if not isinstance(images, list):
        return []
    return [image for image in images if isinstance(image, dict)]


def _get_dependencies(results: dict[str, Any], packages: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    # Maps the package_uid of a dependency to the package_uids of the packages that depend on it.
    # Dependencies that can't be resolved to packages of the project are left out.
    packages_by_purl: dict[str, list[str]] = {}
    for package_uid, package in packages.items():
        if package.get("purl"):
            packages_by_purl.setdefault(_purl_without_qualifiers(package["purl"]), []).append(package_uid)

    dependency_dict: dict[str, list[str]] = {}

    for dependency in results.get("dependencies", []):
        for_package_uid = dependency.get("for_package_uid")
        if for_package_uid not in packages:
            continue

        for resolved_package_uid in _resolve_dependency(dependency, packages, packages_by_purl):
            parents = dependency_dict.setdefault(resolved_package_uid, [])
            if resolved_package_uid != for_package_uid and for_package_uid not in parents:
                parents.append(for_package_uid)

    return dependency_dict


def _resolve_dependency(
    dependency: dict[str, Any], packages: dict[str, dict[str, Any]], packages_by_purl: dict[str, list[str]]
) -> list[str]:
    resolved_to_package_uid = dependency.get("resolved_to_package_uid")
    if resolved_to_package_uid in packages:
        return [resolved_to_package_uid]

    # ScanCode.io resolves dependencies only for some manifests, e.g. not for binaries and installed packages.
    # Their purl has a version, so they belong to the packages with the same purl. The purls of dependencies
    # have no qualifiers, but the purls of packages can have them, e.g. for the architecture.
    purl = dependency.get("purl")
    if not purl:
        return []
    return packages_by_purl.get(_purl_without_qualifiers(purl), [])


def _purl_without_qualifiers(purl: str) -> str:
    return purl.split("#", 1)[0].split("?", 1)[0]


def _get_component_dependencies(
    package_uid: str, packages: dict[str, dict[str, Any]], dependency_dict: dict[str, list[str]]
) -> str:
    dependencies: list[str] = []
    _get_dependencies_recursive(package_uid, packages, dependency_dict, dependencies)

    dependencies.sort()
    return "\n".join(dependencies)


def _get_dependencies_recursive(
    package_uid: str,
    packages: dict[str, dict[str, Any]],
    dependency_dict: dict[str, list[str]],
    dependencies: list[str],
) -> None:
    for parent_uid in dependency_dict.get(package_uid, []):
        dependency = (
            f"{_translate_package_uid(parent_uid, packages)} --> {_translate_package_uid(package_uid, packages)}"
        )
        if dependency not in dependencies:
            dependencies.append(dependency)
            _get_dependencies_recursive(parent_uid, packages, dependency_dict, dependencies)


def _translate_package_uid(package_uid: str, packages: dict[str, dict[str, Any]]) -> str:
    package = packages[package_uid]
    if package.get("version"):
        return f"{package['name']}:{package['version']}"
    return package["name"]


def _get_osv_linux_distribution(distro: dict[str, Any]) -> tuple[str, str]:
    mapping = OSV_LINUX_DISTRIBUTIONS.get(str(distro.get("identifier") or "").lower())
    if not mapping:
        return "", ""

    osv_linux_distribution, get_release = mapping
    version_parts = str(distro.get("version_id") or "").split(".")
    release = get_release(version_parts) if get_release else None
    return osv_linux_distribution, release or ""


def _release_major(version_parts: list[str]) -> Optional[str]:
    if version_parts[0].isdigit():
        return version_parts[0]
    return None


def _release_major_minor(version_parts: list[str]) -> Optional[str]:
    if len(version_parts) >= 2 and version_parts[0].isdigit() and version_parts[1].isdigit():
        return f"{version_parts[0]}.{version_parts[1]}"
    return None


def _release_alpine(version_parts: list[str]) -> Optional[str]:
    release = _release_major_minor(version_parts)
    return f"v{release}" if release else None


def _release_ubuntu(version_parts: list[str]) -> Optional[str]:
    # Same format as used by the OSV parser for Ubuntu purls with a distro qualifier
    release = _release_major_minor(version_parts)
    if release and int(version_parts[0]) % 2 == 0 and version_parts[1] == "04":
        return f"{release}:LTS"
    return release


# Distro identifiers of ScanCode.io, mapped to the OSV distribution and a function to get the release
# from the version of the distro. Distributions without a function have no simple release in OSV,
# so the release stays empty.
OSV_LINUX_DISTRIBUTIONS: dict[str, tuple[str, Optional[Callable[[list[str]], Optional[str]]]]] = {
    "almalinux": (OSVLinuxDistribution.DISTRIBUTION_ALMALINUX, _release_major),
    "alpine": (OSVLinuxDistribution.DISTRIBUTION_ALPINE, _release_alpine),
    "chainguard": (OSVLinuxDistribution.DISTRIBUTION_CHAINGUARD, None),
    "debian": (OSVLinuxDistribution.DISTRIBUTION_DEBIAN, _release_major),
    "mageia": (OSVLinuxDistribution.DISTRIBUTION_MAGEIA, _release_major),
    "opensuse": (OSVLinuxDistribution.DISTRIBUTION_OPENSUSE, None),
    "opensuse-leap": (OSVLinuxDistribution.DISTRIBUTION_OPENSUSE, None),
    "opensuse-tumbleweed": (OSVLinuxDistribution.DISTRIBUTION_OPENSUSE, None),
    "photon": (OSVLinuxDistribution.DISTRIBUTION_PHOTON_OS, _release_major_minor),
    "rhel": (OSVLinuxDistribution.DISTRIBUTION_REDHAT, None),
    "rocky": (OSVLinuxDistribution.DISTRIBUTION_ROCKY_LINUX, _release_major),
    "sles": (OSVLinuxDistribution.DISTRIBUTION_SUSE, None),
    "ubuntu": (OSVLinuxDistribution.DISTRIBUTION_UBUNTU, _release_ubuntu),
    "wolfi": (OSVLinuxDistribution.DISTRIBUTION_WOLFI, None),
}
