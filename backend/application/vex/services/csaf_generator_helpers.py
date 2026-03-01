from typing import Optional

from application.core.models import Branch, Observation, Product
from application.core.types import Status
from application.vex.types import CSAF_Status

VULNERABILITY_ECOSYSTEM = {
    "GHSA": "GitHub Security Advisory",
    "DLA": "Debian Security Bug Tracker ",
    "OSV": "Open Source Vulnerability Database",
    "PYSEC": "Python Packaging Advisory Database",
    "SNYK": "Snyk",
    "RUSTSEC": "Rust Security Advisory Database",
}


# create url for vulnerability
def get_vulnerability_ecosystem(vulnerability_name: str) -> str:
    for key, value in VULNERABILITY_ECOSYSTEM.items():
        if vulnerability_name.startswith(key):
            return value
    return "Unknown ecosystem"


def map_status(secobserve_status: str) -> Optional[str]:
    if secobserve_status in (Status.STATUS_OPEN, Status.STATUS_AFFECTED, Status.STATUS_RISK_ACCEPTED):
        return CSAF_Status.CSAF_STATUS_AFFECTED

    if secobserve_status == Status.STATUS_RESOLVED:
        return CSAF_Status.CSAF_STATUS_FIXED

    if secobserve_status in (
        Status.STATUS_NOT_AFFECTED,
        Status.STATUS_NOT_SECURITY,
        Status.STATUS_FALSE_POSITIVE,
    ):
        return CSAF_Status.CSAF_STATUS_NOT_AFFECTED

    if secobserve_status == Status.STATUS_IN_REVIEW:
        return CSAF_Status.CSAF_STATUS_UNDER_INVESTIGATION

    if secobserve_status == Status.STATUS_DUPLICATE:
        return None

    raise ValueError(f"Invalid status {secobserve_status}")


def get_product_id(product: Product, branch: Optional[Branch]) -> str:
    if branch:
        if branch.purl:
            return branch.purl
        if branch.cpe23:
            return branch.cpe23
        return f"{product.name}:{branch.name}"

    if product.purl:
        return product.purl
    if product.cpe23:
        return product.cpe23
    return product.name


def get_relationship_name(observation: Observation) -> str:
    relationship_name = f"{observation.origin_component_name_version}@"
    relationship_name += (
        f"{observation.product.name}:{observation.branch.name}" if observation.branch else observation.product.name
    )
    return relationship_name


def get_product_or_relationship_id(observation: Observation) -> str:
    if observation.origin_component_name_version:
        return get_relationship_name(observation)
    return get_product_id(observation.product, observation.branch)
