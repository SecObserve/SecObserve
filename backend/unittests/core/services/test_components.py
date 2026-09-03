from application.core.models import Component
from application.core.services.components import (
    _get_identity_hash,
    _prepare_component,
    get_or_create_component,
)
from unittests.base_test_case import BaseTestCase


class TestComponents(BaseTestCase):
    def test_identity_hash_same_purl_different_name(self):
        component_1 = Component(
            name="component_1",
            version="1.0.0",
            name_version="component_1:1.0.0",
            purl="pkg:pypi/django@6.0.7",
        )
        component_2 = Component(
            name="component_2",
            version="2.0.0",
            name_version="component_2:2.0.0",
            purl="pkg:pypi/django@6.0.7",
        )

        self.assertEqual(_get_identity_hash(component_1), _get_identity_hash(component_2))

    def test_identity_hash_different_purl(self):
        component_1 = Component(name="django", purl="pkg:pypi/django@6.0.7")
        component_2 = Component(name="django", purl="pkg:pypi/django@6.0.8")

        self.assertNotEqual(_get_identity_hash(component_1), _get_identity_hash(component_2))

    def test_identity_hash_without_purl_ignores_type_and_cpe(self):
        component_1 = Component(name="component", version="1.0.0", name_version="component:1.0.0")
        component_2 = Component(name="component", version="2.0.0", name_version="component:2.0.0")
        component_3 = Component(name="component", version="1.0.0", name_version="component:1.0.0", type="library")
        component_4 = Component(
            name="component",
            version="1.0.0",
            name_version="component:1.0.0",
            cpe="cpe:2.3:a:vendor:component:1.0.0:*:*:*:*:*:*:*",
        )

        # without a purl the name and the version define the identity, so the same component
        # reported once with and once without a type or a cpe is not split into several components
        self.assertEqual(_get_identity_hash(component_1), _get_identity_hash(component_3))
        self.assertEqual(_get_identity_hash(component_1), _get_identity_hash(component_4))
        self.assertNotEqual(_get_identity_hash(component_1), _get_identity_hash(component_2))

        hashes = {
            _get_identity_hash(component_1),
            _get_identity_hash(component_2),
            _get_identity_hash(component_3),
            _get_identity_hash(component_4),
        }
        self.assertEqual(2, len(hashes))

    def test_prepare_component_valid_purl(self):
        component = Component(name="django", version="6.0.7", purl="pkg:pypi/django@6.0.7")

        _prepare_component(component)

        self.assertEqual("django", component.name)
        self.assertEqual("6.0.7", component.version)
        self.assertEqual("django:6.0.7", component.name_version)
        self.assertEqual("pkg:pypi/django@6.0.7", component.purl)
        self.assertEqual("pypi", component.purl_type)
        self.assertEqual("", component.purl_namespace)

    def test_prepare_component_purl_with_namespace(self):
        component = Component(purl="pkg:deb/ubuntu/curl@8.5.0-2ubuntu10.6")

        _prepare_component(component)

        self.assertEqual("curl", component.name)
        self.assertEqual("8.5.0-2ubuntu10.6", component.version)
        self.assertEqual("curl:8.5.0-2ubuntu10.6", component.name_version)
        self.assertEqual("pkg:deb/ubuntu/curl@8.5.0-2ubuntu10.6", component.purl)
        self.assertEqual("deb", component.purl_type)
        self.assertEqual("ubuntu", component.purl_namespace)

    def test_prepare_component_purl_overwrites_name_and_version(self):
        component = Component(name="wrong_name", version="0.0.1", purl="pkg:pypi/django@6.0.7")

        _prepare_component(component)

        self.assertEqual("django", component.name)
        self.assertEqual("6.0.7", component.version)
        self.assertEqual("django:6.0.7", component.name_version)

    def test_prepare_component_purl_qualifiers_and_subpath_are_cut_off(self):
        component = Component(
            name="curl",
            version="8.5.0-2ubuntu10.6",
            purl="pkg:deb/ubuntu/curl@8.5.0-2ubuntu10.6?arch=amd64&distro=ubuntu-24.04#src/lib",
        )

        _prepare_component(component)

        self.assertEqual("pkg:deb/ubuntu/curl@8.5.0-2ubuntu10.6", component.purl)
        self.assertEqual("deb", component.purl_type)
        self.assertEqual("ubuntu", component.purl_namespace)

    def test_prepare_component_purl_without_version_keeps_name(self):
        component = Component(name="django", purl="pkg:pypi/django?arch=amd64")

        _prepare_component(component)

        self.assertEqual("django", component.name)
        self.assertEqual("", component.version)
        self.assertEqual("django", component.name_version)
        self.assertEqual("pkg:pypi/django", component.purl)
        self.assertEqual("pypi", component.purl_type)

    def test_identity_hash_ignores_purl_qualifiers_and_subpath(self):
        component_1 = get_or_create_component(
            Component(name="curl", version="8.5.0", purl="pkg:deb/ubuntu/curl@8.5.0?arch=amd64")
        )
        component_2 = get_or_create_component(
            Component(name="curl", version="8.5.0", purl="pkg:deb/ubuntu/curl@8.5.0?arch=arm64#src/lib")
        )

        self.assertEqual(component_1.pk, component_2.pk)
        self.assertEqual("pkg:deb/ubuntu/curl@8.5.0", component_1.purl)

    def test_identity_hash_different_purl_namespace(self):
        component_1 = Component(purl="pkg:deb/ubuntu/curl@8.5.0")
        component_2 = Component(purl="pkg:deb/debian/curl@8.5.0")

        _prepare_component(component_1)
        _prepare_component(component_2)

        self.assertNotEqual(_get_identity_hash(component_1), _get_identity_hash(component_2))

    def test_prepare_component_invalid_purl(self):
        component = Component(name="django", version="6.0.7", purl="not_a_purl")

        _prepare_component(component)

        self.assertEqual("django", component.name)
        self.assertEqual("6.0.7", component.version)
        self.assertEqual("", component.purl)
        self.assertEqual("", component.purl_type)
        self.assertEqual("", component.purl_namespace)

    def test_prepare_component_name_version_is_split(self):
        component = Component(name_version="django:6.0.7")

        _prepare_component(component)

        self.assertEqual("django", component.name)
        self.assertEqual("6.0.7", component.version)

    def test_get_or_create_component_is_idempotent(self):
        component_1 = get_or_create_component(Component(name="django", version="6.0.7", purl="pkg:pypi/django@6.0.7"))
        component_2 = get_or_create_component(
            Component(name="other_name", version="6.0.7", purl="pkg:pypi/django@6.0.7")
        )

        self.assertEqual(component_1.pk, component_2.pk)
        self.assertEqual(1, Component.objects.filter(purl="pkg:pypi/django@6.0.7").count())

    def test_get_or_create_component_stores_purl_parts(self):
        component = get_or_create_component(
            Component(name_version="curl:8.5.0", purl="pkg:deb/ubuntu/curl@8.5.0?arch=amd64")
        )

        component_from_db = Component.objects.get(pk=component.pk)
        self.assertEqual("curl", component_from_db.name)
        self.assertEqual("8.5.0", component_from_db.version)
        self.assertEqual("curl:8.5.0", component_from_db.name_version)
        self.assertEqual("pkg:deb/ubuntu/curl@8.5.0", component_from_db.purl)
        self.assertEqual("deb", component_from_db.purl_type)
        self.assertEqual("ubuntu", component_from_db.purl_namespace)

    def test_get_or_create_component_purl_without_version(self):
        component = get_or_create_component(Component(purl="pkg:pypi/django"))

        component_from_db = Component.objects.get(pk=component.pk)
        self.assertEqual("django", component_from_db.name)
        self.assertEqual("", component_from_db.version)
        self.assertEqual("django", component_from_db.name_version)
