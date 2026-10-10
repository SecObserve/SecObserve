from unittest import TestCase

from application.commons.services.export import _escape_formula


class TestEscapeFormula(TestCase):
    def test_none_value(self):
        self.assertIsNone(_escape_formula(None))

    def test_non_string_value(self):
        self.assertEqual(_escape_formula(123), 123)
        self.assertEqual(_escape_formula(12.34), 12.34)
        self.assertEqual(_escape_formula([]), [])
        self.assertEqual(_escape_formula({}), {})

    def test_empty_string(self):
        self.assertEqual(_escape_formula(""), "")

    def test_normal_string(self):
        self.assertEqual(_escape_formula("Hello World"), "Hello World")

    def test_formula_injection_equals(self):
        self.assertEqual(_escape_formula("=SUM(A1:B2)"), "'=SUM(A1:B2)")

    def test_formula_injection_plus(self):
        self.assertEqual(_escape_formula("+SUM(A1:B2)"), "'+SUM(A1:B2)")

    def test_formula_injection_minus(self):
        self.assertEqual(_escape_formula("-SUM(A1:B2)"), "'-SUM(A1:B2)")

    def test_formula_injection_at(self):
        self.assertEqual(_escape_formula("@SUM(A1:B2)"), "'@SUM(A1:B2)")

    def test_formula_injection_tab(self):
        self.assertEqual(_escape_formula("\tSUM(A1:B2)"), "'\tSUM(A1:B2)")

    def test_formula_injection_carriage_return(self):
        self.assertEqual(_escape_formula("\rSUM(A1:B2)"), "'\rSUM(A1:B2)")

    def test_formula_not_at_start(self):
        self.assertEqual(_escape_formula("1=SUM(A1:B2)"), "1=SUM(A1:B2)")

    def test_special_characters_inside(self):
        self.assertEqual(_escape_formula("A=B+C"), "A=B+C")
