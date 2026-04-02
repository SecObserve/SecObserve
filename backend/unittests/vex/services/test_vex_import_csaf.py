from os import path

from application.core.models import Observation
from application.vex.models import VEX_Document
from application.vex.services.vex_import import import_vex
from application.vex.types import VEX_Document_Type
from unittests.vex.services.basetest_vex_import import BaseTestVEXImport


class TestVEXImportCSAF(BaseTestVEXImport):
    def test_import_long_long(self):
        self.load_vex_test()

        with open(path.dirname(__file__) + "/files/so_csaf_2020_0001_0001.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0001_0001",
                author="SecObserve",
            )
            self.check_vex_document(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF)

            self.check_product()

    def test_import_long_short(self):
        self.load_vex_test()

        with open(path.dirname(__file__) + "/files/so_csaf_2020_0001_0001_short.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0001_0001",
                author="SecObserve",
            )
            self.check_vex_document(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF, short=True)

            self.check_product()

    def test_import_short_long(self):
        self.load_vex_test(short=True)

        with open(path.dirname(__file__) + "/files/so_csaf_2020_0001_0001.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0001_0001",
                author="SecObserve",
            )
            self.check_vex_document(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF)

            self.check_product(short=True)

    def test_import_short_short(self):
        self.load_vex_test(short=True)

        with open(path.dirname(__file__) + "/files/so_csaf_2020_0001_0001_short.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0001_0001",
                author="SecObserve",
            )
            self.check_vex_document(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF, short=True)

            self.check_product(short=True)

    def test_import_without_component_long_long(self):
        self.load_vex_test()

        with open(path.dirname(__file__) + "/files/so_csaf_without_component.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0002_0001",
                author="SecObserve",
            )
            self.check_vex_document_without_component_purl(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF)

            self.check_product()

    def test_import_without_component_long_short(self):
        self.load_vex_test()

        with open(path.dirname(__file__) + "/files/so_csaf_without_component_short.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0002_0001",
                author="SecObserve",
            )
            self.check_vex_document_without_component_purl(
                vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF, short=True
            )

            self.check_product()

    def test_import_without_component_short_long(self):
        self.load_vex_test(short=True)

        with open(path.dirname(__file__) + "/files/so_csaf_without_component.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0002_0001",
                author="SecObserve",
            )
            self.check_vex_document_without_component_purl(vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF)

            self.check_product(short=True)

    def test_import_without_component_short_short(self):
        self.load_vex_test(short=True)

        with open(path.dirname(__file__) + "/files/so_csaf_without_component_short.json") as testfile:
            import_vex(testfile)

            vex_document = VEX_Document.objects.get(
                document_id="https://csaf.example.com/so_2020_0002_0001",
                author="SecObserve",
            )
            self.check_vex_document_without_component_purl(
                vex_document, VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF, short=True
            )

            self.check_product(short=True)
