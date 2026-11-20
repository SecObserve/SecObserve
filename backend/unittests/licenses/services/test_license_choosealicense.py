import tarfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import requests

from application.licenses.models import License
from application.licenses.services.license_choosealicense import (
    import_choosealicense,
)
from unittests.base_test_case import BaseTestCase

ROOT = "choosealicense.com-gh-pages"

RULES = """
permissions:
- description: The licensed material may be modified.
  label: Modification
  tag: modifications
conditions:
- description: A copy of the license and copyright notice must be included.
  label: License and copyright notice
  tag: include-copyright
limitations:
- description: This license includes a limitation of liability.
  label: Liability
  tag: liability
"""


def _license_file(spdx_id: str, description: str = "A license.", conditions: str = "include-copyright") -> str:
    return (
        "---\n"
        "title: Test license\n"
        f"spdx-id: {spdx_id}\n"
        f"description: {description}\n"
        "permissions:\n"
        "  - modifications\n"
        "conditions:\n"
        f"  - {conditions}\n"
        "limitations:\n"
        "  - liability\n"
        "---\n"
        "\n"
        "License text\n"
    )


def _archive(files: dict[str, str], directories: list[str] | None = None, symlinks: list[str] | None = None) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in directories or []:
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            archive.addfile(info)
        for name in symlinks or []:
            info = tarfile.TarInfo(name)
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            archive.addfile(info)
        for name, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, BytesIO(data))
    return buffer.getvalue()


MODIFICATION = {
    "tag": "modifications",
    "label": "Modification",
    "description": "The licensed material may be modified.",
}
COPYRIGHT = {
    "tag": "include-copyright",
    "label": "License and copyright notice",
    "description": "A copy of the license and copyright notice must be included.",
}
LIABILITY = {
    "tag": "liability",
    "label": "Liability",
    "description": "This license includes a limitation of liability.",
}


class TestImportChoosealicense(BaseTestCase):
    def setUp(self):
        super().setUp()
        # The patch is started here instead of decorating the class, because other test classes
        # change patch.TEST_PREFIX, which would make a class decorator patch setUpClass as well.
        patcher = patch("application.licenses.services.license_choosealicense.requests.get")
        self.addCleanup(patcher.stop)
        self.mock_get = patcher.start()
        self.mock_get.side_effect = self._get

        self.license_1 = License.objects.create(spdx_id="Test-CAL-1", name="Test CAL 1")
        self.license_2 = License.objects.create(spdx_id="Test-CAL-2", name="Test CAL 2")

        self.files = {
            f"{ROOT}/_data/rules.yml": RULES,
            f"{ROOT}/_licenses/test-cal-1.txt": _license_file("Test-CAL-1", "First license."),
        }

    def _get(self, url: str, timeout: int) -> MagicMock:  # pylint: disable=unused-argument
        response = MagicMock()
        response.content = _archive(self.files)
        return response

    def test_import(self):
        result = import_choosealicense()

        self.assertIn("choosealicense.com: licenses updated: 1, cleared: 0", result)
        self.license_1.refresh_from_db()
        self.assertEqual("test-cal-1", self.license_1.choosealicense_key)
        self.assertEqual("First license.", self.license_1.choosealicense_description)
        self.assertEqual([MODIFICATION], self.license_1.choosealicense_permissions)
        self.assertEqual([COPYRIGHT], self.license_1.choosealicense_conditions)
        self.assertEqual([LIABILITY], self.license_1.choosealicense_limitations)
        self.license_2.refresh_from_db()
        self.assertEqual("", self.license_2.choosealicense_key)

    def test_import_unchanged(self):
        import_choosealicense()

        result = import_choosealicense()

        self.assertIn("choosealicense.com: licenses updated: 0, cleared: 0", result)

    def test_import_deprecated_spdx_id(self):
        only = License.objects.create(spdx_id="Test-CAL-3-only", name="Test CAL 3 only")
        or_later = License.objects.create(spdx_id="Test-CAL-3-or-later", name="Test CAL 3 or later")
        self.files[f"{ROOT}/_licenses/test-cal-3.txt"] = _license_file("Test-CAL-3", "Third license.")
        self.files[f"{ROOT}/_licenses/test-cal-3-only.txt"] = _license_file("Test-CAL-3-only", "Own entry.")

        import_choosealicense()

        only.refresh_from_db()
        self.assertEqual("test-cal-3-only", only.choosealicense_key)
        self.assertEqual("Own entry.", only.choosealicense_description)
        or_later.refresh_from_db()
        self.assertEqual("test-cal-3", or_later.choosealicense_key)
        self.assertEqual("Third license.", or_later.choosealicense_description)

    def test_import_unknown_tag(self):
        self.files[f"{ROOT}/_licenses/test-cal-1.txt"] = _license_file("Test-CAL-1", conditions="new-condition")

        import_choosealicense()

        self.license_1.refresh_from_db()
        self.assertEqual(
            [{"tag": "new-condition", "label": "new-condition", "description": ""}],
            self.license_1.choosealicense_conditions,
        )

    def test_import_skips_invalid_files(self):
        self.files[f"{ROOT}/_licenses/no-front-matter.txt"] = "Just a license text\n"
        self.files[f"{ROOT}/_licenses/no-spdx-id.txt"] = "---\ntitle: No SPDX id\n---\nText\n"
        self.files[f"{ROOT}/_licenses/invalid-yaml.txt"] = "---\nspdx-id: [unclosed\n---\nText\n"
        self.files[f"{ROOT}/_licenses/unterminated.txt"] = "---\nspdx-id: Test-CAL-2\n"

        with self.assertLogs("secobserve.licenses", level="WARNING") as logs:
            result = import_choosealicense()

        self.assertEqual(4, len(logs.output))
        self.assertIn("choosealicense.com: licenses updated: 1, cleared: 0", result)
        self.license_2.refresh_from_db()
        self.assertEqual("", self.license_2.choosealicense_key)

    def test_import_ignores_unexpected_entries(self):
        self.files[f"{ROOT}/other/test-cal-2.txt"] = _license_file("Test-CAL-2")
        self.files[f"{ROOT}/_licenses/nested/test-cal-2.txt"] = _license_file("Test-CAL-2")
        self.files[f"{ROOT}/_licenses/test-cal-2.md"] = _license_file("Test-CAL-2")
        self.files["_licenses/test-cal-2.txt"] = _license_file("Test-CAL-2")

        def get(url: str, timeout: int) -> MagicMock:  # pylint: disable=unused-argument
            response = MagicMock()
            response.content = _archive(
                self.files,
                directories=[f"{ROOT}/_licenses/test-cal-x.txt"],
                symlinks=[f"{ROOT}/_licenses/test-cal-y.txt"],
            )
            return response

        self.mock_get.side_effect = get

        result = import_choosealicense()

        self.assertIn("choosealicense.com: licenses updated: 1, cleared: 0", result)
        self.license_2.refresh_from_db()
        self.assertEqual("", self.license_2.choosealicense_key)

    def test_import_clears_unmatched_license(self):
        self.license_2.choosealicense_key = "old"
        self.license_2.choosealicense_description = "Old description."
        self.license_2.choosealicense_permissions = [MODIFICATION]
        self.license_2.save()

        result = import_choosealicense()

        self.assertIn("choosealicense.com: licenses updated: 1, cleared: 1", result)
        self.license_2.refresh_from_db()
        self.assertEqual("", self.license_2.choosealicense_key)
        self.assertEqual("", self.license_2.choosealicense_description)
        self.assertEqual([], self.license_2.choosealicense_permissions)

    def test_import_download_fails(self):
        self.license_1.choosealicense_key = "old"
        self.license_1.save()
        self.mock_get.side_effect = requests.ConnectionError("connection failed")

        with self.assertRaises(requests.ConnectionError):
            import_choosealicense()

        self.license_1.refresh_from_db()
        self.assertEqual("old", self.license_1.choosealicense_key)

    def test_import_without_rules(self):
        del self.files[f"{ROOT}/_data/rules.yml"]

        with self.assertRaises(ValueError):
            import_choosealicense()
