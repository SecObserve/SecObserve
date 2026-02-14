import unittest
from unittest.mock import MagicMock, patch

from application.rules.services.rego_interpreter import RegoException, RegoInterpreter


class TestRegoException(unittest.TestCase):
    def test_message(self):
        exception = RegoException("test error")
        self.assertEqual(exception.message, "test error")

    def test_is_exception(self):
        exception = RegoException("test error")
        self.assertIsInstance(exception, Exception)


class TestRegoInterpreterInit(unittest.TestCase):

    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_init_success(self, mock_interpreter_cls):
        mock_interpreter = MagicMock()
        mock_interpreter_cls.return_value = mock_interpreter
        mock_bundle = MagicMock()
        mock_interpreter.build.return_value = mock_bundle

        rego_module = "package rule\ndefault allow = false"
        interpreter = RegoInterpreter(rego_module)

        self.assertEqual(interpreter.policy, rego_module)
        self.assertEqual(interpreter.rego_bundle, mock_bundle)
        self.assertEqual(mock_interpreter.log_level, 1)
        mock_interpreter.add_module.assert_called_once_with("rule", rego_module)
        mock_interpreter.build.assert_called_once_with("data")

    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_init_rego_error(self, mock_interpreter_cls):
        from regopy.rego_shared import RegoError

        mock_interpreter = MagicMock()
        mock_interpreter_cls.return_value = mock_interpreter
        mock_interpreter.add_module.side_effect = RegoError("syntax error")

        with self.assertRaises(RegoException) as context:
            RegoInterpreter("invalid rego")

        self.assertIn("Error while building rego bundle", context.exception.message)
        self.assertIn("syntax error", context.exception.message)


class TestRegoInterpreterQuery(unittest.TestCase):

    @patch("application.rules.services.rego_interpreter.Interpreter")
    def setUp(self, mock_interpreter_cls):
        mock_interpreter = MagicMock()
        mock_interpreter_cls.return_value = mock_interpreter
        mock_interpreter.build.return_value = MagicMock()
        self.interpreter = RegoInterpreter("package rule")
        self.mock_bundle = self.interpreter.rego_bundle

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_success(self, mock_interpreter_cls, mock_input_cls):
        mock_input = MagicMock()
        mock_input_cls.return_value = mock_input

        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run

        expected_result = {"severity": "High", "status": "Open"}
        mock_expression = MagicMock()
        mock_expression.get.return_value = expected_result
        mock_node = MagicMock()
        mock_node.expressions = [mock_expression]
        mock_output = MagicMock()
        mock_output.results = [mock_node]
        mock_rego_run.query_bundle.return_value = mock_output

        data = {"title": "test"}
        result = self.interpreter.query(data)

        self.assertEqual(result, expected_result)
        mock_input_cls.assert_called_once_with(data)
        mock_rego_run.set_input.assert_called_once_with(mock_input)
        mock_rego_run.query_bundle.assert_called_once_with(self.mock_bundle)
        mock_expression.get.assert_called_once_with("rule")

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_with_none_data(self, mock_interpreter_cls, mock_input_cls):
        mock_input = MagicMock()
        mock_input_cls.return_value = mock_input

        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run

        expected_result = {"severity": "Low"}
        mock_expression = MagicMock()
        mock_expression.get.return_value = expected_result
        mock_node = MagicMock()
        mock_node.expressions = [mock_expression]
        mock_output = MagicMock()
        mock_output.results = [mock_node]
        mock_rego_run.query_bundle.return_value = mock_output

        result = self.interpreter.query()

        self.assertEqual(result, expected_result)
        mock_input_cls.assert_called_once_with(None)

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_no_results(self, mock_interpreter_cls, mock_input_cls):
        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run

        mock_output = MagicMock()
        mock_output.results = []
        mock_rego_run.query_bundle.return_value = mock_output

        with self.assertRaises(RegoException) as context:
            self.interpreter.query({"title": "test"})

        self.assertEqual(context.exception.message, "Rego output has no results")

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_no_results_none(self, mock_interpreter_cls, mock_input_cls):
        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run

        mock_output = MagicMock()
        mock_output.results = None
        mock_rego_run.query_bundle.return_value = mock_output

        with self.assertRaises(RegoException) as context:
            self.interpreter.query({"title": "test"})

        self.assertEqual(context.exception.message, "Rego output has no results")

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_no_expressions(self, mock_interpreter_cls, mock_input_cls):
        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run

        mock_node = MagicMock()
        mock_node.expressions = []
        mock_output = MagicMock()
        mock_output.results = [mock_node]
        mock_rego_run.query_bundle.return_value = mock_output

        with self.assertRaises(RegoException) as context:
            self.interpreter.query({"title": "test"})

        self.assertEqual(context.exception.message, "Rego results have no expressions")

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_no_rule_element(self, mock_interpreter_cls, mock_input_cls):
        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run

        mock_expression = MagicMock()
        mock_expression.get.return_value = None
        mock_node = MagicMock()
        mock_node.expressions = [mock_expression]
        mock_output = MagicMock()
        mock_output.results = [mock_node]
        mock_rego_run.query_bundle.return_value = mock_output

        with self.assertRaises(RegoException) as context:
            self.interpreter.query({"title": "test"})

        self.assertEqual(context.exception.message, "Rego expressions have no 'rule' element")

    @patch("application.rules.services.rego_interpreter.Input")
    @patch("application.rules.services.rego_interpreter.Interpreter")
    def test_query_rego_error(self, mock_interpreter_cls, mock_input_cls):
        from regopy.rego_shared import RegoError

        mock_rego_run = MagicMock()
        mock_interpreter_cls.return_value = mock_rego_run
        mock_rego_run.query_bundle.side_effect = RegoError("query failed")

        with self.assertRaises(RegoException) as context:
            self.interpreter.query({"title": "test"})

        self.assertIn("Error while querying rego module", context.exception.message)
        self.assertIn("query failed", context.exception.message)
