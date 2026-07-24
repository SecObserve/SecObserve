from unittest.mock import MagicMock

from django.test import SimpleTestCase

from application.core.models import Product
from application.licenses.models import License_Component
from application.licenses.signals import (
    license_component_post_delete,
    license_component_post_save,
)


class TestLicenseSignals(SimpleTestCase):
    def test_raw_component_load_does_not_update_product_timestamp(self) -> None:
        product = MagicMock(spec=Product)
        component = MagicMock(spec=License_Component)
        component.product = product

        license_component_post_save(License_Component, component, created=True, raw=True)

        product.save.assert_not_called()

    def test_component_delete_updates_product_timestamp(self) -> None:
        product = MagicMock(spec=Product)
        component = MagicMock(spec=License_Component)
        component.product = product

        license_component_post_delete(License_Component, component, origin=component)

        product.save.assert_called_once_with()

    def test_product_cascade_skips_redundant_product_update(self) -> None:
        product = MagicMock(spec=Product)
        component = MagicMock(spec=License_Component)
        component.product = product

        license_component_post_delete(License_Component, component, origin=product)

        product.save.assert_not_called()
