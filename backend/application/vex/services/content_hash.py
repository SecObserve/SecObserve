import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any


def calculate_vex_content_hash(content: Any) -> str:
    content_json = json.dumps(_to_primitive(content))
    return hashlib.sha256(content_json.casefold().encode("utf-8").strip()).hexdigest()


def _to_primitive(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_primitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_primitive(item) for item in value)
    if isinstance(value, dict):
        return {key: _to_primitive(item) for key, item in value.items()}
    return value
