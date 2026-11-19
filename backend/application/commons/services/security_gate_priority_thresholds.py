from typing import Any

_KEYS = {"priority", "threshold"}


def _is_int_between(value: Any, minimum: int, maximum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def normalize_security_gate_priority_thresholds(value: Any) -> list[dict[str, int]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Priority thresholds must be a list")

    result: dict[int, int] = {}
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError("Each priority threshold must be an object with priority and threshold")
        for key in entry:
            if key not in _KEYS:
                raise ValueError(f"Unknown key '{key}'")
        priority: Any = entry.get("priority")
        if not _is_int_between(priority, 1, 99):
            raise ValueError("Priority must be a number between 1 and 99")
        threshold: Any = entry.get("threshold")
        if not _is_int_between(threshold, 0, 999999):
            raise ValueError("Threshold must be a number between 0 and 999999")
        if priority in result:
            raise ValueError(f"Priority {priority} is listed twice")
        result[priority] = threshold

    return [{"priority": priority, "threshold": result[priority]} for priority in sorted(result)]
