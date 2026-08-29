import hashlib

from packageurl import PackageURL

from application.core.models import Component


def get_identity_hash(component: Component) -> str:
    hash_string = _get_string_to_hash(component)
    return hashlib.sha256(hash_string.casefold().encode("utf-8").strip()).hexdigest()


def _get_string_to_hash(component: Component) -> str:
    if component.purl:
        return component.purl

    hash_string = component.name_version
    if component.type:
        hash_string += component.type
    if component.cpe:
        hash_string += component.cpe
    return hash_string


def prepare_component(component: Component) -> None:
    _prepare_name_version(component)

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
    if component.cpe is None:
        component.cpe = ""

    if component.purl:
        try:
            purl = PackageURL.from_string(component.purl)
            component.purl_type = purl.type
        except ValueError:
            component.purl = ""
            component.purl_type = ""

    if component.purl_type is None:
        component.purl_type = ""


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


def get_or_create_component(component: Component) -> Component:
    prepare_component(component)
    component.identity_hash = get_identity_hash(component)

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
            "cpe": component.cpe,
        },
    )
    return existing_component
