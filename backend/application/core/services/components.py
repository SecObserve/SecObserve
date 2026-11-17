import hashlib
from itertools import batched
from typing import Optional

from packageurl import PackageURL

from application.core.models import Component


def get_or_create_component(component: Component) -> Optional[Component]:
    if not component.name and not component.purl:
        return None

    _prepare_component(component)
    component.identity_hash = _get_identity_hash(component)

    # type(component) instead of Component, so that data migrations can pass an instance of the
    # historical model from apps.get_model() and have the row written through that model.
    existing_component, _ = type(component).objects.get_or_create(
        identity_hash=component.identity_hash,
        defaults={
            "name": component.name,
            "version": component.version,
            "name_version": component.name_version,
            "type": component.type,
            "purl": component.purl,
            "purl_type": component.purl_type,
            "purl_namespace": component.purl_namespace,
        },
    )
    return existing_component


COMPONENTS_BATCH_SIZE = 500


def get_or_create_components(components: list[Component]) -> list[Optional[Component]]:
    """
    Batch version of get_or_create_component: needs a few queries for all components
    instead of one or two per component. The result is aligned with the given list,
    None for components without name and purl.
    """
    identity_hashes: list[Optional[str]] = []
    components_to_store: dict[str, Component] = {}
    for component in components:
        if not component.name and not component.purl:
            identity_hashes.append(None)
            continue

        _prepare_component(component)
        component.identity_hash = _get_identity_hash(component)
        identity_hashes.append(component.identity_hash)
        components_to_store.setdefault(component.identity_hash, component)

    stored_components = _get_components_by_identity_hashes(list(components_to_store.keys()))

    missing_components = [
        component for identity_hash, component in components_to_store.items() if identity_hash not in stored_components
    ]
    if missing_components:
        # ignore_conflicts, because a concurrent import might have created some of the components.
        # The primary keys are not returned with ignore_conflicts, so the components are read again.
        Component.objects.bulk_create(missing_components, batch_size=COMPONENTS_BATCH_SIZE, ignore_conflicts=True)
        stored_components.update(
            _get_components_by_identity_hashes([component.identity_hash for component in missing_components])
        )

    return [stored_components.get(identity_hash) if identity_hash else None for identity_hash in identity_hashes]


def _get_components_by_identity_hashes(identity_hashes: list[str]) -> dict[str, Component]:
    components: dict[str, Component] = {}
    for batch in batched(identity_hashes, COMPONENTS_BATCH_SIZE):
        for component in Component.objects.filter(identity_hash__in=batch):
            components[component.identity_hash] = component
    return components


def _get_identity_hash(component: Component) -> str:
    hash_string = _get_string_to_hash(component)
    return hashlib.sha256(hash_string.casefold().encode("utf-8").strip()).hexdigest()


def _get_string_to_hash(component: Component) -> str:
    if component.purl:
        return component.purl

    return component.name_version


def _prepare_component(component: Component) -> None:
    if component.name_version is None:
        component.name_version = ""
    if component.name is None:
        component.name = ""
    if component.version is None:
        component.version = ""
    if component.type is None:
        component.type = ""
    if component.purl is None:
        component.purl = ""

    if component.purl:
        try:
            purl = PackageURL.from_string(component.purl)

            component.name_version = ""
            component.name = purl.name
            component.version = purl.version if purl.version else ""
            component.purl_type = purl.type
            component.purl_namespace = purl.namespace if purl.namespace else ""

            component.purl = PackageURL(
                type=purl.type,
                namespace=purl.namespace,
                name=purl.name,
                version=purl.version,
            ).to_string()
        except ValueError:
            component.purl = ""
            component.purl_type = ""
            component.purl_namespace = ""

    if component.purl_type is None:
        component.purl_type = ""
    if component.purl_namespace is None:
        component.purl_namespace = ""

    _prepare_name_version(component)


def _prepare_name_version(component: Component) -> None:
    if not component.name_version:
        if component.name and component.version:
            component.name_version = component.name + ":" + component.version
        elif component.name:
            component.name_version = component.name
    else:
        component_parts = component.name_version.split(":")
        if len(component_parts) == 3:
            component.name = f"{component_parts[0]}:{component_parts[1]}"
            component.version = component_parts[2]
        elif len(component_parts) == 2:
            component.name = component_parts[0]
            component.version = component_parts[1]
        elif len(component_parts) == 1:
            component.name = component.name_version
            component.version = ""
