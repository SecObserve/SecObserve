from os import path

from application.vex.models import VEX_Document
from application.vex.services.vex_import import import_vex
from application.vex.types import VEX_Document_Type
from unittests.vex.services.basetest_vex_import import BaseTestVEXImport


class TestVEXImportOpenVEX(BaseTestVEXImport):
    def test_import(self):
        self.load_vex_test()

        with open(path.dirname(__file__) + "/files/so_openvex_2020_0001_0001.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://openvex.example.com/so_openvex_2020_0001",
                author="SecObserve",
            )
            self.check_vex_document(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_OPENVEX)

            self.check_product()

    def test_import_without_component(self):
        self.load_vex_test()

        with open(path.dirname(__file__) + "/files/so_openvex_without_component.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://openvex.example.com/so_openvex_2020_0002",
                author="SecObserve",
            )
            self.check_vex_document_without_component_purl(
                vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_OPENVEX
            )

            self.check_product()
