from typing import Optional

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from application.core.models import Branch, Observation, Product
from application.core.queries.observation import get_observations
from application.core.queries.product import get_product_by_id
from application.core.types import VEX_Justification
from application.vex.models import VEX_Counter


def create_document_base_id(document_id_prefix: str) -> str:
    year = timezone.now().year
    with transaction.atomic():
        counter = VEX_Counter.objects.select_for_update().get_or_create(
            document_id_prefix=document_id_prefix, year=year
        )[0]
        counter.counter += 1
        counter.save()
    return f"{counter.year}_{counter.counter:04d}"


def check_product_or_vulnerabilities(product: Optional[Product], vulnerability_names: list[str]) -> None:
    if not product and not vulnerability_names:
        raise ValidationError("Either product or vulnerabilities or both must be set")


def check_and_get_product(product_id: int) -> Optional[Product]:
    if not product_id:
        return None

    product = get_product_by_id(product_id, is_product_group=False)
    if not product:
        raise ValidationError(f"Product with id {product_id} does not exist")

    return product


def check_vulnerability_names(vulnerability_names: list[str]) -> None:
    if not vulnerability_names:
        return

    for vulnerability_name in vulnerability_names:
        if not Observation.objects.filter(vulnerability_id=vulnerability_name).exists():
            raise ValidationError(f"Vulnerability with name {vulnerability_name} does not exist")


def check_branches(branches: list[int], product: Optional[Product]) -> list[Branch]:
    if not branches:
        return []

    if not product:
        raise ValidationError("Product must be set when using branch_names")

    product_branches = Branch.objects.filter(id__in=branches, product=product)
    if len(product_branches) != len(branches):
        raise ValidationError(f"Some of the branches do not exist for product {product.name}")

    return list(product_branches)


def check_branch_names(branch_names: list[str], product: Optional[Product]) -> list[Branch]:
    if not branch_names:
        return []

    if not product:
        raise ValidationError("Product must be set when using branch_names")

    branches = Branch.objects.filter(name__in=branch_names, product=product)
    if len(branch_names) != len(branches):
        raise ValidationError("Some of the branch names do not exist")

    return list(branches)


def get_observations_for_vulnerability(
    vulnerability_name: str,
) -> list[Observation]:
    return list(get_observations().filter(vulnerability_id=vulnerability_name).order_by("id"))


def get_observations_for_vulnerabilities(
    vulnerability_names: list[str],
) -> list[Observation]:
    return list(get_observations().filter(vulnerability_id__in=vulnerability_names).order_by("id"))


def get_observations_for_product(
    product: Product, vulnerability_names: list[str], branches: list[Branch]
) -> list[Observation]:
    observations = get_observations().filter(product_id=product.pk).exclude(vulnerability_id="").order_by("id")

    if vulnerability_names:
        observations = observations.filter(vulnerability_id__in=vulnerability_names)

    if branches:
        observations = observations.filter(branch__in=branches)

    return list(observations)


def get_product_id(observation: Observation) -> str:
    if observation.branch:
        if observation.branch.purl:
            return observation.branch.purl
        if observation.branch.cpe23:
            return observation.branch.cpe23
        return f"{observation.product.name}:{observation.branch.name}"

    if observation.product.purl:
        return observation.product.purl
    if observation.product.cpe23:
        return observation.product.cpe23
    return observation.product.name


def get_component_id(observation: Observation) -> str:
    if observation.origin_component_purl:
        return observation.origin_component_purl
    if observation.origin_component_cpe:
        return observation.origin_component_cpe
    return ""


VULNERABILITY_URLS = {
    "CVE": "https://nvd.nist.gov/vuln/detail/",
    "DLA": "https://security-tracker.debian.org/tracker/",
    "GHSA": "https://github.com/advisories/",
    "OSV": "https://osv.dev/vulnerability/",
    "PYSEC": "https://osv.dev/vulnerability/",
    "SNYK": "https://snyk.io/vuln/",
    "RUSTSEC": "https://rustsec.org/advisories/",
}


# create url for vulnerability
def get_vulnerability_url(vulnerability_name: str) -> Optional[str]:
    for key, value in VULNERABILITY_URLS.items():
        if vulnerability_name.startswith(key):
            return value + vulnerability_name
    return None


def map_vex_justification_to_csaf_openvex_justification(justification: str) -> str:
    mapping = {
        VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT: VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_PRESENT: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_PRESENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_IN_EXECUTE_PATH: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_IN_EXECUTE_PATH,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_INLINE_MITIGATIONS_ALREADY_EXIST: VEX_Justification.JUSTIFICATION_INLINE_MITIGATIONS_ALREADY_EXIST,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_CODE_NOT_PRESENT: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_PRESENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_CODE_NOT_REACHABLE: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_IN_EXECUTE_PATH,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_DEPENDENCY: VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_ENVIRONMENT: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_BY_COMPILER: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_AT_RUNTIME: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_AT_PERIMETER: VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_BY_MITIGATING_CONTROL: VEX_Justification.JUSTIFICATION_INLINE_MITIGATIONS_ALREADY_EXIST,  # noqa: E501 pylint: disable=line-too-long
    }
    return mapping.get(justification, "")
