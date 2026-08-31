from application.core.models import Component
from application.core.services.components import (
    get_identity_hash,
    get_or_create_component,
    prepare_component,
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

        self.assertEqual(get_identity_hash(component_1), get_identity_hash(component_2))

    def test_identity_hash_different_purl(self):
        component_1 = Component(name="django", purl="pkg:pypi/django@6.0.7")
        component_2 = Component(name="django", purl="pkg:pypi/django@6.0.8")

        self.assertNotEqual(get_identity_hash(component_1), get_identity_hash(component_2))

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
        self.assertEqual(get_identity_hash(component_1), get_identity_hash(component_3))
        self.assertEqual(get_identity_hash(component_1), get_identity_hash(component_4))
        self.assertNotEqual(get_identity_hash(component_1), get_identity_hash(component_2))

        hashes = {
            get_identity_hash(component_1),
            get_identity_hash(component_2),
            get_identity_hash(component_3),
            get_identity_hash(component_4),
        }
        self.assertEqual(2, len(hashes))

    def test_prepare_component_valid_purl(self):
        component = Component(name="django", version="6.0.7", purl="pkg:pypi/django@6.0.7")

        prepare_component(component)

        self.assertEqual("django:6.0.7", component.name_version)
        self.assertEqual("pkg:pypi/django@6.0.7", component.purl)
        self.assertEqual("pypi", component.purl_type)

    def test_prepare_component_invalid_purl(self):
        component = Component(name="django", version="6.0.7", purl="not_a_purl")

        prepare_component(component)

        self.assertEqual("", component.purl)
        self.assertEqual("", component.purl_type)

    def test_prepare_component_name_version_is_split(self):
        component = Component(name_version="django:6.0.7")

        prepare_component(component)

        self.assertEqual("django", component.name)
        self.assertEqual("6.0.7", component.version)

    def test_get_or_create_component_is_idempotent(self):
        component_1 = get_or_create_component(Component(name="django", version="6.0.7", purl="pkg:pypi/django@6.0.7"))
        component_2 = get_or_create_component(
            Component(name="other_name", version="6.0.7", purl="pkg:pypi/django@6.0.7")
        )

        self.assertEqual(component_1.pk, component_2.pk)
        self.assertEqual(1, Component.objects.filter(purl="pkg:pypi/django@6.0.7").count())
