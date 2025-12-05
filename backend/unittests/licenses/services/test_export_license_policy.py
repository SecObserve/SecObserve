from django.core.management import call_command

from application.licenses.models import License, License_Policy, License_Policy_Item
from application.licenses.services.export_license_policy_sbom_utility import (
    export_license_policy_sbom_utility,
)
from application.licenses.services.export_license_policy_secobserve import (
    export_license_policy_secobserve_json,
    export_license_policy_secobserve_yaml,
)
from application.licenses.types import License_Policy_Evaluation_Result
from unittests.base_test_case import BaseTestCase


class TestLicenseGroupMemberSerializer(BaseTestCase):
    @classmethod
    def setUpClass(self):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )

        license_policy = License_Policy.objects.get(pk=1000)
        license_policy.description = "description_1000"
        license_policy.ignore_component_types = "apk, oci"
        license_policy.save()
        License_Policy_Item(
            license_policy=license_policy,
            license=License.objects.get(pk=1),
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        ).save()
        License_Policy_Item(
            license_policy=license_policy,
            license_expression="MIT OR 3BSD",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED,
        ).save()
        License_Policy_Item(
            license_policy=license_policy,
            non_spdx_license="Non-SPDX",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
        ).save()
        License_Policy_Item(
            license_policy=license_policy,
            non_spdx_license="Ignored license",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_IGNORED,
            comment="Ignored license comment",
        ).save()
        License_Policy_Item(
            license_policy=license_policy,
            non_spdx_license="Unknown license",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            comment="Unknown license comment",
        ).save()

        self.license_policy_with_parent = License_Policy(name="license_policy_with_parent", parent=license_policy)
        self.license_policy_with_parent.save()

        License_Policy_Item(
            license_policy=self.license_policy_with_parent,
            license=License.objects.get(pk=1),
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED,
            comment="Permissive license",
        ).save()
        License_Policy_Item(
            license_policy=self.license_policy_with_parent,
            license_expression="MIT OR 3BSD",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED,
            comment="Permissive license expression",
        ).save()
        License_Policy_Item(
            license_policy=self.license_policy_with_parent,
            non_spdx_license="Non-SPDX",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED,
            comment="Permissive non-SPDX license",
        ).save()
        License_Policy_Item(
            license_policy=self.license_policy_with_parent,
            non_spdx_license="Another non-SPDX",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN,
            comment="Forbidden non-SPDX license",
        ).save()

        super().setUpClass()

    def test_export_json(self):
        license_policy = License_Policy.objects.get(pk=1000)
        json_data = export_license_policy_secobserve_json(license_policy)

        json_data_expected = """{
    "description": "description_1000",
    "ignore_component_types": [
        "apk",
        "oci"
    ],
    "items": [
        {
            "evaluation_result": "Allowed",
            "from_parent": false,
            "license_group": "Permissive Model (Blue Oak Council)",
            "spdx_license": "BlueOak-1.0.0"
        },
        {
            "evaluation_result": "Forbidden",
            "from_parent": false,
            "spdx_license": "0BSD"
        },
        {
            "evaluation_result": "Review required",
            "from_parent": false,
            "license_expression": "MIT OR 3BSD"
        },
        {
            "evaluation_result": "Forbidden",
            "from_parent": false,
            "non_spdx_license": "Non-SPDX"
        },
        {
            "comment": "Ignored license comment",
            "evaluation_result": "Ignored",
            "from_parent": false,
            "non_spdx_license": "Ignored license"
        },
        {
            "comment": "Unknown license comment",
            "evaluation_result": "Unknown",
            "from_parent": false,
            "non_spdx_license": "Unknown license"
        }
    ],
    "name": "public"
}"""
        self.assertEqual(json_data_expected, json_data)

    def test_export_yaml(self):
        license_policy = License_Policy.objects.get(pk=1000)
        yaml_data = export_license_policy_secobserve_yaml(license_policy)

        yaml_data_expected = """description: description_1000
ignore_component_types:
- apk
- oci
items:
- evaluation_result: Allowed
  from_parent: false
  license_group: Permissive Model (Blue Oak Council)
  spdx_license: BlueOak-1.0.0
- evaluation_result: Forbidden
  from_parent: false
  spdx_license: 0BSD
- evaluation_result: Review required
  from_parent: false
  license_expression: MIT OR 3BSD
- evaluation_result: Forbidden
  from_parent: false
  non_spdx_license: Non-SPDX
- comment: Ignored license comment
  evaluation_result: Ignored
  from_parent: false
  non_spdx_license: Ignored license
- comment: Unknown license comment
  evaluation_result: Unknown
  from_parent: false
  non_spdx_license: Unknown license
name: public
"""
        self.assertEqual(yaml_data_expected, yaml_data)

    def test_export_json_with_parent(self):
        json_data = export_license_policy_secobserve_json(self.license_policy_with_parent)

        json_data_expected = """{
    "description": "",
    "items": [
        {
            "evaluation_result": "Allowed",
            "from_parent": true,
            "license_group": "Permissive Model (Blue Oak Council)",
            "spdx_license": "BlueOak-1.0.0"
        },
        {
            "comment": "Permissive license",
            "evaluation_result": "Allowed",
            "from_parent": false,
            "spdx_license": "0BSD"
        },
        {
            "comment": "Permissive license expression",
            "evaluation_result": "Allowed",
            "from_parent": false,
            "license_expression": "MIT OR 3BSD"
        },
        {
            "comment": "Permissive non-SPDX license",
            "evaluation_result": "Allowed",
            "from_parent": false,
            "non_spdx_license": "Non-SPDX"
        },
        {
            "comment": "Ignored license comment",
            "evaluation_result": "Ignored",
            "from_parent": true,
            "non_spdx_license": "Ignored license"
        },
        {
            "comment": "Unknown license comment",
            "evaluation_result": "Unknown",
            "from_parent": true,
            "non_spdx_license": "Unknown license"
        },
        {
            "comment": "Forbidden non-SPDX license",
            "evaluation_result": "Forbidden",
            "from_parent": false,
            "non_spdx_license": "Another non-SPDX"
        }
    ],
    "name": "license_policy_with_parent",
    "parent": "public"
}"""
        self.assertEqual(json_data_expected, json_data)

    def test_export_yaml_with_parent(self):
        yaml_data = export_license_policy_secobserve_yaml(self.license_policy_with_parent)

        yaml_data_expected = """description: ''
items:
- evaluation_result: Allowed
  from_parent: true
  license_group: Permissive Model (Blue Oak Council)
  spdx_license: BlueOak-1.0.0
- comment: Permissive license
  evaluation_result: Allowed
  from_parent: false
  spdx_license: 0BSD
- comment: Permissive license expression
  evaluation_result: Allowed
  from_parent: false
  license_expression: MIT OR 3BSD
- comment: Permissive non-SPDX license
  evaluation_result: Allowed
  from_parent: false
  non_spdx_license: Non-SPDX
- comment: Ignored license comment
  evaluation_result: Ignored
  from_parent: true
  non_spdx_license: Ignored license
- comment: Unknown license comment
  evaluation_result: Unknown
  from_parent: true
  non_spdx_license: Unknown license
- comment: Forbidden non-SPDX license
  evaluation_result: Forbidden
  from_parent: false
  non_spdx_license: Another non-SPDX
name: license_policy_with_parent
parent: public
"""
        self.assertEqual(yaml_data_expected, yaml_data)

    def test_export_sbom_utility(self):
        license_policy = License_Policy.objects.get(pk=1000)
        json_data = export_license_policy_sbom_utility(license_policy)

        json_data_expected = """{
    "policies": [
        {
            "annotationRefs": [
                "ALLOWED"
            ],
            "deprecated": false,
            "family": "BlueOak-1-0-0",
            "id": "BlueOak-1.0.0",
            "name": "Blue Oak Model License 1.0.0",
            "osi": true,
            "reference": "https://spdx.org/licenses/BlueOak-1.0.0.html",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "FORBIDDEN"
            ],
            "deprecated": false,
            "family": "0BSD",
            "id": "0BSD",
            "name": "BSD Zero Clause License",
            "osi": true,
            "reference": "https://spdx.org/licenses/0BSD.html",
            "usagePolicy": "deny"
        },
        {
            "annotationRefs": [
                "REVIEW REQUIRED"
            ],
            "deprecated": false,
            "family": "MIT-OR-3BSD",
            "id": "",
            "name": "MIT OR 3BSD",
            "osi": false,
            "reference": "",
            "usagePolicy": "needs-review"
        },
        {
            "annotationRefs": [
                "FORBIDDEN"
            ],
            "deprecated": false,
            "family": "Non-SPDX",
            "id": "",
            "name": "Non-SPDX",
            "osi": false,
            "reference": "",
            "usagePolicy": "deny"
        },
        {
            "annotationRefs": [
                "IGNORED"
            ],
            "deprecated": false,
            "family": "Ignored-license",
            "id": "",
            "name": "Ignored license",
            "notes": [
                "Ignored license comment"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "UNKNOWN"
            ],
            "deprecated": false,
            "family": "Unknown-license",
            "id": "",
            "name": "Unknown license",
            "notes": [
                "Unknown license comment"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "needs-review"
        }
    ]
}"""
        self.assertEqual(json_data_expected, json_data)

    def test_export_sbom_utility_with_parent(self):
        json_data = export_license_policy_sbom_utility(self.license_policy_with_parent)

        json_data_expected = """{
    "policies": [
        {
            "annotationRefs": [
                "ALLOWED"
            ],
            "deprecated": false,
            "family": "BlueOak-1-0-0",
            "id": "BlueOak-1.0.0",
            "name": "Blue Oak Model License 1.0.0",
            "osi": true,
            "reference": "https://spdx.org/licenses/BlueOak-1.0.0.html",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "ALLOWED"
            ],
            "deprecated": false,
            "family": "0BSD",
            "id": "0BSD",
            "name": "BSD Zero Clause License",
            "notes": [
                "Permissive license"
            ],
            "osi": true,
            "reference": "https://spdx.org/licenses/0BSD.html",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "ALLOWED"
            ],
            "deprecated": false,
            "family": "MIT-OR-3BSD",
            "id": "",
            "name": "MIT OR 3BSD",
            "notes": [
                "Permissive license expression"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "ALLOWED"
            ],
            "deprecated": false,
            "family": "Non-SPDX",
            "id": "",
            "name": "Non-SPDX",
            "notes": [
                "Permissive non-SPDX license"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "IGNORED"
            ],
            "deprecated": false,
            "family": "Ignored-license",
            "id": "",
            "name": "Ignored license",
            "notes": [
                "Ignored license comment"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "allow"
        },
        {
            "annotationRefs": [
                "UNKNOWN"
            ],
            "deprecated": false,
            "family": "Unknown-license",
            "id": "",
            "name": "Unknown license",
            "notes": [
                "Unknown license comment"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "needs-review"
        },
        {
            "annotationRefs": [
                "FORBIDDEN"
            ],
            "deprecated": false,
            "family": "Another-non-SPDX",
            "id": "",
            "name": "Another non-SPDX",
            "notes": [
                "Forbidden non-SPDX license"
            ],
            "osi": false,
            "reference": "",
            "usagePolicy": "deny"
        }
    ]
}"""
        self.assertEqual(json_data_expected, json_data)
