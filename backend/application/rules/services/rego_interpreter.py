from typing import Any, Optional

from regopy import Input, Interpreter
from regopy.rego_shared import RegoError


class RegoException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class RegoInterpreter:
    def __init__(self, rego_module: str) -> None:
        self.policy = rego_module
        try:
            rego = Interpreter()
            rego.log_level = 1
            rego.add_module("rule", rego_module)
            self.rego_bundle = rego.build("data")
        except RegoError as e:
            raise RegoException(f"Error while building rego bundle: {str(e)}") from e

    def query(self, data: Optional[Any] = None) -> dict:
        try:
            rego_run = Interpreter()
            rego_run.set_input(Input(data))
            output = rego_run.query_bundle(self.rego_bundle)

            node = output.results
            if not node:
                raise RegoException("Rego output has no results")
            if not node[0].expressions:
                raise RegoException("Rego results have no expressions")
            result = node[0].expressions[0].get("rule")
            if result is None:
                raise RegoException("Rego expressions have no 'rule' element")
            return result
        except RegoError as e:
            raise RegoException(f"Error while querying rego module: {str(e)}") from e
