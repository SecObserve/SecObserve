import logging
import tarfile
from io import BytesIO
from typing import Any, Optional

import requests
import yaml

from application.licenses.models import License

logger = logging.getLogger("secobserve.licenses")

CHOOSEALICENSE_ARCHIVE_URL = "https://codeload.github.com/github/choosealicense.com/tar.gz/refs/heads/gh-pages"

MAX_ARCHIVE_SIZE = 10 * 1024 * 1024
MAX_FILE_SIZE = 1024 * 1024

LICENSES_DIRECTORY = "_licenses"
LICENSE_SUFFIX = ".txt"
RULES_DIRECTORY = "_data"
RULES_FILE = "rules.yml"

RULE_CATEGORIES = ["permissions", "conditions", "limitations"]
SPDX_ID_SUFFIXES = ["-only", "-or-later"]

CHOOSEALICENSE_FIELDS = [
    "choosealicense_key",
    "choosealicense_description",
    "choosealicense_permissions",
    "choosealicense_conditions",
    "choosealicense_limitations",
]


def import_choosealicense() -> str:
    license_files, rules_file = _get_files()
    rules = _parse_rules(rules_file)

    entries: dict[str, dict[str, Any]] = {}
    for key, content in license_files.items():
        front_matter = _parse_front_matter(content)
        spdx_id = front_matter.get("spdx-id") if front_matter else None
        if not front_matter or not isinstance(spdx_id, str) or not spdx_id:
            logger.warning("choosealicense.com license %s has no valid front matter with spdx-id", key)
            continue
        entries[spdx_id] = _get_values(key, front_matter, rules)

    licenses = {spdx_license.spdx_id: spdx_license for spdx_license in License.objects.all()}
    assignments = _match_licenses(entries, licenses)

    licenses_updated = 0
    licenses_cleared = 0
    empty_values = _get_values("", {}, rules)

    for spdx_id, spdx_license in licenses.items():
        values = assignments.get(spdx_id, empty_values)
        changed_fields = [field for field in CHOOSEALICENSE_FIELDS if getattr(spdx_license, field) != values[field]]
        if not changed_fields:
            continue

        if values["choosealicense_key"]:
            licenses_updated += 1
        else:
            licenses_cleared += 1

        for field in changed_fields:
            setattr(spdx_license, field, values[field])
        spdx_license.save(update_fields=changed_fields)

    return f"choosealicense.com: licenses updated: {licenses_updated}, cleared: {licenses_cleared}"


def _get_files() -> tuple[dict[str, str], str]:
    response = requests.get(CHOOSEALICENSE_ARCHIVE_URL, timeout=60)
    response.raise_for_status()
    if len(response.content) > MAX_ARCHIVE_SIZE:
        raise ValueError("choosealicense.com archive is too large")

    license_files: dict[str, str] = {}
    rules_file = ""
    # The archive is only read in memory, nothing is extracted to the file system
    with tarfile.open(fileobj=BytesIO(response.content), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or member.size > MAX_FILE_SIZE:
                continue

            # Expected paths are <root>/_licenses/<key>.txt and <root>/_data/rules.yml
            parts = member.name.split("/")
            if len(parts) != 3:
                continue
            directory, filename = parts[1], parts[2]

            is_license = directory == LICENSES_DIRECTORY and filename.endswith(LICENSE_SUFFIX)
            is_rules = directory == RULES_DIRECTORY and filename == RULES_FILE
            if not is_license and not is_rules:
                continue

            extracted_file = archive.extractfile(member)
            if not extracted_file:
                continue
            content = extracted_file.read().decode("utf-8")

            if is_license:
                key = filename.removesuffix(LICENSE_SUFFIX)
                if key:
                    license_files[key] = content
            else:
                rules_file = content

    if not rules_file:
        raise ValueError(f"choosealicense.com archive has no {RULES_DIRECTORY}/{RULES_FILE}")

    return license_files, rules_file


def _parse_rules(rules_file: str) -> dict[str, dict[str, dict[str, str]]]:
    data = yaml.safe_load(rules_file)
    if not isinstance(data, dict):
        raise ValueError("choosealicense.com rules are not a YAML mapping")

    rules: dict[str, dict[str, dict[str, str]]] = {}
    for category in RULE_CATEGORIES:
        rules[category] = {}
        for rule in data.get(category) or []:
            if isinstance(rule, dict) and isinstance(rule.get("tag"), str):
                rules[category][rule["tag"]] = {
                    "tag": rule["tag"],
                    "label": str(rule.get("label") or rule["tag"]),
                    "description": str(rule.get("description") or ""),
                }
    return rules


def _parse_front_matter(content: str) -> Optional[dict[str, Any]]:
    lines = content.lstrip("﻿").replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            try:
                front_matter = yaml.safe_load("\n".join(lines[1:index]))
            except yaml.YAMLError:
                return None
            return front_matter if isinstance(front_matter, dict) else None

    return None


def _get_values(key: str, front_matter: dict[str, Any], rules: dict[str, dict[str, dict[str, str]]]) -> dict[str, Any]:
    values: dict[str, Any] = {
        "choosealicense_key": key[:64],
        "choosealicense_description": str(front_matter.get("description") or "").strip()[:2048],
    }
    for category in RULE_CATEGORIES:
        values[f"choosealicense_{category}"] = [
            rules[category].get(tag, {"tag": tag, "label": tag, "description": ""})
            for tag in front_matter.get(category) or []
            if isinstance(tag, str)
        ]
    return values


def _match_licenses(entries: dict[str, dict[str, Any]], licenses: dict[str, License]) -> dict[str, dict[str, Any]]:
    assignments = {spdx_id: values for spdx_id, values in entries.items() if spdx_id in licenses}

    # choosealicense.com uses some deprecated SPDX ids, e.g. GPL-3.0 for GPL-3.0-only and GPL-3.0-or-later
    for spdx_id, values in entries.items():
        if any(spdx_id.endswith(suffix) for suffix in SPDX_ID_SUFFIXES):
            continue
        for suffix in SPDX_ID_SUFFIXES:
            derived_spdx_id = spdx_id + suffix
            if derived_spdx_id in licenses and derived_spdx_id not in assignments:
                assignments[derived_spdx_id] = values

    return assignments
