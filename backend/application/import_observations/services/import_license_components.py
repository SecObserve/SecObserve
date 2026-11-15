import hashlib
from datetime import datetime
from itertools import batched
from typing import Optional, Tuple

from django.db import connection
from django.db.models import Field
from django.db.models.functions import MD5
from django.utils import timezone

from application.commons.services.functions import (
    clip_fields,
    get_comma_separated_as_list,
)
from application.core.models import Product
from application.import_observations.models import Vulnerability_Check
from application.licenses.models import (
    License_Component,
    License_Component_Evidence,
)
from application.licenses.services.concluded_license import ConcludeLicenseApplicator
from application.licenses.services.license_component import (
    prepare_license_component,
    set_core_components,
    set_effective_license,
)
from application.licenses.services.license_policy import (
    apply_license_policy_product,
    apply_license_policy_to_component,
    get_license_evaluation_results_for_product,
    get_license_policy,
)
from application.licenses.services.licenselynx import apply_licenselynx
from application.licenses.services.spdx_license_cache import SPDXLicenseCache
from application.licenses.types import (
    NO_LICENSE_INFORMATION,
    License_Policy_Evaluation_Result,
)

SBOM_BULK_BATCH_SIZE = 100

# Fields copied from the imported license component to the existing one
LICENSE_COMPONENT_IMPORTED_FIELDS = (
    "component_type",
    "component_purl",
    "component_purl_type",
    "component_cpe",
    "component_dependencies",
    "component_cyclonedx_bom_link",
    "component_url",
    "component_copyright",
    "imported_declared_license_name",
    "imported_declared_spdx_license",
    "imported_declared_license_expression",
    "imported_declared_non_spdx_license",
    "imported_declared_multiple_licenses",
    "imported_concluded_license_name",
    "imported_concluded_spdx_license",
    "imported_concluded_license_expression",
    "imported_concluded_non_spdx_license",
    "imported_concluded_multiple_licenses",
)

# Fields set by the evaluation of the license, last_change is set when one of them changes
LICENSE_COMPONENT_EFFECTIVE_FIELDS = (
    "effective_license_name",
    "effective_spdx_license",
    "effective_license_expression",
    "effective_non_spdx_license",
    "effective_multiple_licenses",
    "evaluation_result",
)

# Fields that can change for an existing license component during an import,
# besides import_last_seen and last_change
LICENSE_COMPONENT_UPDATE_FIELDS = (
    ("component",)
    + LICENSE_COMPONENT_IMPORTED_FIELDS
    + (
        "manual_concluded_license_name",
        "manual_concluded_spdx_license",
        "manual_concluded_license_expression",
        "manual_concluded_non_spdx_license",
        "manual_concluded_comment",
    )
    + LICENSE_COMPONENT_EFFECTIVE_FIELDS
    + ("numerical_evaluation_result",)
)

LICENSE_COMPONENT_UPDATE_BATCH_SIZE = 500


def _get_attnames(field_names: tuple[str, ...]) -> tuple[str, ...]:
    # attname is the id of a foreign key, so comparing the values doesn't load the referenced objects
    attnames = []
    for field_name in field_names:
        field = License_Component._meta.get_field(field_name)
        attnames.append(field.attname if isinstance(field, Field) else field_name)
    return tuple(attnames)


LICENSE_COMPONENT_UPDATE_ATTNAMES = _get_attnames(LICENSE_COMPONENT_UPDATE_FIELDS)
LICENSE_COMPONENT_EFFECTIVE_ATTNAMES = _get_attnames(LICENSE_COMPONENT_EFFECTIVE_FIELDS)


class _LicenseEvaluator:
    def __init__(self, product: Product, spdx_cache: SPDXLicenseCache) -> None:
        self.spdx_cache = spdx_cache
        self.concluded_license_applicator = ConcludeLicenseApplicator(product)
        self.license_policy = get_license_policy(product)
        self.license_evaluation_results = (
            get_license_evaluation_results_for_product(product) if self.license_policy else {}
        )
        self.ignore_component_types = (
            get_comma_separated_as_list(self.license_policy.ignore_component_types) if self.license_policy else []
        )

    def evaluate(self, component: License_Component) -> None:
        set_effective_license(component)
        if (
            not component.manual_concluded_license_name
            or component.manual_concluded_license_name == NO_LICENSE_INFORMATION
        ):
            self.concluded_license_applicator.apply_concluded_license(component)
            set_effective_license(component)

        apply_licenselynx(component, self.spdx_cache)

        clip_fields("licenses", "License_Component", component)

        # The license policy is applied here as well, to write the final result with the import.
        # Without it, apply_license_policy_product would have to update the components again.
        if self.license_policy:
            apply_license_policy_to_component(
                component, self.license_evaluation_results, self.ignore_component_types, self.spdx_cache
            )
        else:
            component.evaluation_result = License_Policy_Evaluation_Result.RESULT_UNKNOWN


def process_license_components(  # pylint: disable=too-many-locals
    license_components: list[License_Component],
    scanner: str,
    vulnerability_check: Vulnerability_Check,
) -> Tuple[int, int, int]:
    now = timezone.now()

    existing_components_dict: dict[str, License_Component] = {
        existing_component.identity_hash: existing_component
        for existing_component in License_Component.objects.filter(
            product=vulnerability_check.product,
            branch=vulnerability_check.branch,
            origin_service=vulnerability_check.service,
            upload_filename=vulnerability_check.filename,
        ).select_related("effective_spdx_license", "manual_concluded_spdx_license")
    }
    existing_evidences = _get_existing_license_evidences(vulnerability_check)

    spdx_cache = SPDXLicenseCache()
    unique_components = _prepare_license_components(license_components, spdx_cache)

    set_core_components(
        [
            unsaved_component
            for unsaved_component in unique_components
            if _needs_core_component(unsaved_component, existing_components_dict.get(unsaved_component.identity_hash))
        ]
    )

    license_evaluator = _LicenseEvaluator(vulnerability_check.product, spdx_cache)

    components_new: list[License_Component] = []
    components_changed: list[License_Component] = []
    unchanged_component_ids: list[int] = []
    components_updated = 0
    evidences_new: list[License_Component_Evidence] = []
    evidence_ids_deleted: list[int] = []

    for unsaved_component in unique_components:
        existing_component = existing_components_dict.pop(unsaved_component.identity_hash, None)
        if existing_component:
            components_updated += 1

            if _update_existing_license_component(existing_component, unsaved_component, license_evaluator, now):
                components_changed.append(existing_component)
            else:
                unchanged_component_ids.append(existing_component.pk)

            evidences_to_create, evidence_ids_to_delete = _diff_license_evidences(
                unsaved_component, existing_component, existing_evidences.get(existing_component.pk, [])
            )
            evidences_new += evidences_to_create
            evidence_ids_deleted += evidence_ids_to_delete
        else:
            unsaved_component.product = vulnerability_check.product
            unsaved_component.branch = vulnerability_check.branch
            unsaved_component.origin_service = vulnerability_check.service
            unsaved_component.upload_filename = vulnerability_check.filename
            unsaved_component.import_last_seen = now
            unsaved_component.last_change = now

            license_evaluator.evaluate(unsaved_component)
            components_new.append(unsaved_component)

    # Unchanged components only need the new import_last_seen, which is much cheaper than a bulk_update
    for batch in batched(unchanged_component_ids, LICENSE_COMPONENT_UPDATE_BATCH_SIZE):
        License_Component.objects.filter(pk__in=batch).update(import_last_seen=now)

    License_Component.objects.bulk_update(
        components_changed,
        list(LICENSE_COMPONENT_UPDATE_FIELDS) + ["import_last_seen", "last_change"],
        SBOM_BULK_BATCH_SIZE,
    )

    evidences_new += _create_license_components(components_new, vulnerability_check)

    for batch in batched(evidence_ids_deleted, LICENSE_COMPONENT_UPDATE_BATCH_SIZE):
        License_Component_Evidence.objects.filter(pk__in=batch).delete()
    License_Component_Evidence.objects.bulk_create(evidences_new, SBOM_BULK_BATCH_SIZE)

    # Components that have not been found in the import are deleted, their evidences are deleted by cascade
    components_deleted = len(existing_components_dict)
    License_Component.objects.filter(
        pk__in=[existing_component.pk for existing_component in existing_components_dict.values()]
    ).delete()

    _update_vulnerability_check(
        vulnerability_check, scanner, (len(components_new), components_updated, components_deleted)
    )

    # The components of this import have already been evaluated, but other components of the branch might
    # not reflect the current license policy yet. Only components with a changed evaluation are written.
    apply_license_policy_product(spdx_cache, vulnerability_check.product, vulnerability_check.branch)

    return len(components_new), components_updated, components_deleted


def _update_vulnerability_check(
    vulnerability_check: Vulnerability_Check, scanner: str, numbers: Tuple[int, int, int]
) -> None:
    if numbers == (0, 0, 0):
        vulnerability_check.last_import_licenses_new = None
        vulnerability_check.last_import_licenses_updated = None
        vulnerability_check.last_import_licenses_deleted = None
    else:
        (
            vulnerability_check.last_import_licenses_new,
            vulnerability_check.last_import_licenses_updated,
            vulnerability_check.last_import_licenses_deleted,
        ) = numbers

        vulnerability_check.product.last_license_change = timezone.now()
        vulnerability_check.product.save()

    if scanner:
        vulnerability_check.scanner = scanner
    vulnerability_check.save()


def _prepare_license_components(
    license_components: list[License_Component], spdx_cache: SPDXLicenseCache
) -> list[License_Component]:
    unique_components: list[License_Component] = []
    processed_hashes: set[str] = set()

    for unsaved_component in license_components:
        prepare_license_component(unsaved_component, spdx_cache)
        if unsaved_component.identity_hash not in processed_hashes:
            processed_hashes.add(unsaved_component.identity_hash)
            unique_components.append(unsaved_component)

    return unique_components


def _needs_core_component(
    unsaved_component: License_Component, existing_component: Optional[License_Component]
) -> bool:
    """
    Core components are only needed for new license components, for existing ones without a core component
    and for existing ones whose core component might have changed. The identity of a license component
    doesn't contain the purl, but the identity of a core component does, so a changed purl can lead to
    a different core component.
    """
    return (
        existing_component is None
        or existing_component.component_id is None
        or existing_component.component_purl != unsaved_component.component_purl
        or existing_component.component_name_version != unsaved_component.component_name_version
    )


def _update_existing_license_component(
    existing_component: License_Component,
    unsaved_component: License_Component,
    license_evaluator: _LicenseEvaluator,
    now: datetime,
) -> bool:
    """Returns True if the existing component has been changed and needs to be written."""

    values_before = _get_license_component_values(existing_component, LICENSE_COMPONENT_UPDATE_ATTNAMES)
    effective_values_before = _get_license_component_values(existing_component, LICENSE_COMPONENT_EFFECTIVE_ATTNAMES)

    # Must be checked before the imported fields are copied, because it compares them
    if _needs_core_component(unsaved_component, existing_component):
        existing_component.component = unsaved_component.component
    for field_name in LICENSE_COMPONENT_IMPORTED_FIELDS:
        setattr(existing_component, field_name, getattr(unsaved_component, field_name))

    license_evaluator.evaluate(existing_component)

    existing_component.import_last_seen = now
    if values_before == _get_license_component_values(existing_component, LICENSE_COMPONENT_UPDATE_ATTNAMES):
        return False

    if effective_values_before != _get_license_component_values(
        existing_component, LICENSE_COMPONENT_EFFECTIVE_ATTNAMES
    ):
        existing_component.last_change = now

    return True


def _get_license_component_values(component: License_Component, attnames: tuple[str, ...]) -> tuple:
    return tuple(getattr(component, attname) for attname in attnames)


def _create_license_components(
    components_new: list[License_Component], vulnerability_check: Vulnerability_Check
) -> list[License_Component_Evidence]:
    """Creates the new license components and returns their evidences, which still need to be created."""

    inserted_components = License_Component.objects.bulk_create(components_new, SBOM_BULK_BATCH_SIZE)

    license_component_evidences: list[License_Component_Evidence] = []

    if connection.vendor == "mysql":
        # MySQL doesn't support RETURNING, so bulk_create returns objects without PKs.
        # Re-fetch by identity_hash to get real PKs before creating evidences.
        components_needing_evidences = [c for c in components_new if c.unsaved_evidences]
        if components_needing_evidences:
            inserted_hashes = [c.identity_hash for c in components_needing_evidences]
            inserted_by_hash = {
                c.identity_hash: c
                for c in License_Component.objects.filter(
                    identity_hash__in=inserted_hashes,
                    product=vulnerability_check.product,
                    branch=vulnerability_check.branch,
                    origin_service=vulnerability_check.service,
                    upload_filename=vulnerability_check.filename,
                )
            }
            for component in components_needing_evidences:
                db_component = inserted_by_hash.get(component.identity_hash)
                if db_component:
                    license_component_evidences += _process_license_evidences(component, db_component)
    else:
        for inserted_component in inserted_components:
            license_component_evidences += _process_license_evidences(inserted_component, inserted_component)

    return license_component_evidences


def _get_existing_license_evidences(
    vulnerability_check: Vulnerability_Check,
) -> dict[int, list[tuple[int, str, str]]]:
    """
    Reads the evidences of all license components of the vulnerability check in one query and returns
    them by license component id. Like for the observations, only the hash of the evidence is read.
    """
    existing_evidences: dict[int, list[tuple[int, str, str]]] = {}

    for evidence_id, license_component_id, name, evidence_md5 in (
        License_Component_Evidence.objects.filter(
            license_component__product=vulnerability_check.product,
            license_component__branch=vulnerability_check.branch,
            license_component__origin_service=vulnerability_check.service,
            license_component__upload_filename=vulnerability_check.filename,
        )
        .annotate(evidence_md5=MD5("evidence"))
        .values_list("pk", "license_component_id", "name", "evidence_md5")
    ):
        existing_evidences.setdefault(license_component_id, []).append((evidence_id, name, evidence_md5))

    return existing_evidences


def _diff_license_evidences(
    unsaved_component: License_Component,
    existing_component: License_Component,
    existing_evidences: list[tuple[int, str, str]],
) -> Tuple[list[License_Component_Evidence], list[int]]:
    """
    Compares the imported evidences with the stored ones, by name and hash of the evidence.
    Returns the evidences to be created and the ids of the evidences to be deleted.
    """

    remaining_evidence_ids: dict[tuple[str, str], list[int]] = {}
    for evidence_id, name, evidence_md5 in existing_evidences:
        remaining_evidence_ids.setdefault((name, evidence_md5), []).append(evidence_id)

    evidences_to_create = []
    for imported_evidence in _process_license_evidences(unsaved_component, existing_component):
        evidence_ids = remaining_evidence_ids.get((imported_evidence.name, _md5(imported_evidence.evidence)))
        if evidence_ids:
            evidence_ids.pop()
        else:
            evidences_to_create.append(imported_evidence)

    evidence_ids_to_delete = [
        evidence_id for evidence_ids in remaining_evidence_ids.values() for evidence_id in evidence_ids
    ]

    return evidences_to_create, evidence_ids_to_delete


def _process_license_evidences(
    source_component: License_Component, target_component: License_Component
) -> list[License_Component_Evidence]:
    license_component_evidences = []

    if source_component.unsaved_evidences:
        for unsaved_evidence in source_component.unsaved_evidences:
            evidence = License_Component_Evidence(
                license_component=target_component,
                name=unsaved_evidence[0],
                evidence=unsaved_evidence[1],
            )
            clip_fields("licenses", "License_Component_Evidence", evidence)
            license_component_evidences.append(evidence)

    return license_component_evidences


def _md5(value: str) -> str:
    # Same as the MD5 function of the database, only used to detect changes
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()
