from rest_framework.exceptions import ValidationError

from application.commons.services.functions import validate_vex_remediations
from unittests.base_test_case import BaseTestCase


class TestValidateVexRemediations(BaseTestCase):
    def test_validate_vex_remediations_null_value(self):
        result = validate_vex_remediations(None)
        self.assertIsNone(result)

    def test_validate_vex_remediations_empty_list(self):
        result = validate_vex_remediations([])
        self.assertIsNone(result)

    def test_validate_vex_remediations_empty_item(self):
        value = [{}]
        result = validate_vex_remediations(value)
        self.assertIsNone(result)

    def test_validate_vex_remediations_valid_single_item(self):
        value = [{"category": "fixed", "text": "This issue is fixed."}]
        result = validate_vex_remediations(value)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category"], "fixed")
        self.assertEqual(result[0]["text"], "This issue is fixed.")

    def test_validate_vex_remediations_valid_multiple_items(self):
        value = [
            {"category": "fixed", "text": "This issue is fixed."},
            {"category": "mitigated", "text": "This issue is mitigated."},
        ]
        result = validate_vex_remediations(value)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)

    def test_validate_vex_remediations_non_list_string(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations("invalid")
        self.assertIn("must be a list", str(context.exception))

    def test_validate_vex_remediations_non_list_dict(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations({"category": "fixed"})
        self.assertIn("must be a list", str(context.exception))

    def test_validate_vex_remediations_non_list_int(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations(123)
        self.assertIn("must be a list", str(context.exception))

    def test_validate_vex_remediations_item_not_dict(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations(["not a dict"])
        self.assertIn("must be a dictionary", str(context.exception))

    def test_validate_vex_remediations_item_missing_category_field(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations([{"text": "some text"}])
        self.assertIn("must contain the fields", str(context.exception))

    def test_validate_vex_remediations_item_missing_text_field(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations([{"category": "fixed"}])
        self.assertIn("must contain the fields", str(context.exception))

    def test_validate_vex_remediations_item_category_not_string(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations([{"category": 123, "text": "some text"}])
        self.assertIn("category", str(context.exception))

    def test_validate_vex_remediations_item_text_not_string(self):
        with self.assertRaises(ValidationError) as context:
            validate_vex_remediations([{"category": "fixed", "text": 123}])
        self.assertIn("text", str(context.exception))

    def test_validate_vex_remediations_item_with_extra_fields(self):
        value = [{"category": "fixed", "text": "This is fixed.", "extra_field": "ignored"}]
        result = validate_vex_remediations(value)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category"], "fixed")

    def test_validate_vex_remediations_mixed_valid_and_invalid_items(self):
        with self.assertRaises(ValidationError):
            validate_vex_remediations(
                [
                    {"category": "fixed", "text": "Valid item."},
                    {"category": 123, "text": "Invalid category."},
                ]
            )
