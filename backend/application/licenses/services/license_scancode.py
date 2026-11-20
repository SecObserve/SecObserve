import logging
from typing import Any

import requests

from application.licenses.models import License

logger = logging.getLogger("secobserve.licenses")

SCANCODE_LICENSEDB_URL = "https://scancode-licensedb.aboutcode.org"

SCANCODE_FIELDS = [
    "scancode_key",
    "scancode_category",
    "scancode_owner",
    "scancode_homepage_url",
    "scancode_osi_url",
    "scancode_faq_url",
    "scancode_text_urls",
]


def enrich_licenses_from_scancode(index: list[dict[str, Any]]) -> str:
    licenses = {spdx_license.spdx_id: spdx_license for spdx_license in License.objects.all()}
    matches = _match_licenses(index, licenses)

    licenses_enriched = 0
    licenses_failed = 0
    handled_spdx_ids: set[str] = set()

    with requests.Session() as session:
        for entry, matched_licenses in matches:
            handled_spdx_ids.update(spdx_license.spdx_id for spdx_license in matched_licenses)
            try:
                details = _get_details(session, entry)
            except (requests.RequestException, ValueError) as e:
                logger.warning("Cannot get ScanCode LicenseDB details for %s: %s", entry.get("license_key"), str(e))
                licenses_failed += 1
                continue

            values = _get_values(entry, details)
            for spdx_license in matched_licenses:
                if _set_values(spdx_license, values):
                    licenses_enriched += 1

    licenses_cleared = 0
    empty_values = _get_values({}, {})
    for spdx_id, spdx_license in licenses.items():
        if spdx_id not in handled_spdx_ids and spdx_license.scancode_key:
            _set_values(spdx_license, empty_values)
            licenses_cleared += 1

    return (
        f"ScanCode LicenseDB: licenses enriched: {licenses_enriched}, "
        + f"cleared: {licenses_cleared}, failed: {licenses_failed}"
    )


def _match_licenses(
    index: list[dict[str, Any]], licenses: dict[str, License]
) -> list[tuple[dict[str, Any], list[License]]]:
    matches: dict[str, tuple[dict[str, Any], list[License]]] = {}
    matched_spdx_ids: set[str] = set()

    # Primary SPDX keys first, so they win over other SPDX keys of a different entry
    for entry in index:
        spdx_license = licenses.get(entry.get("spdx_license_key") or "")
        if spdx_license and entry.get("license_key"):
            matches.setdefault(entry["license_key"], (entry, []))[1].append(spdx_license)
            matched_spdx_ids.add(spdx_license.spdx_id)

    for entry in index:
        if not entry.get("license_key"):
            continue
        for other_spdx_license_key in entry.get("other_spdx_license_keys") or []:
            if not other_spdx_license_key or other_spdx_license_key.startswith("LicenseRef-"):
                continue
            spdx_license = licenses.get(other_spdx_license_key)
            if spdx_license and spdx_license.spdx_id not in matched_spdx_ids:
                matches.setdefault(entry["license_key"], (entry, []))[1].append(spdx_license)
                matched_spdx_ids.add(spdx_license.spdx_id)

    return list(matches.values())


def _get_details(session: requests.Session, entry: dict[str, Any]) -> dict[str, Any]:
    filename = entry.get("json") or f"{entry['license_key']}.json"
    response = session.get(f"{SCANCODE_LICENSEDB_URL}/{filename}", timeout=60)
    response.raise_for_status()
    details = response.json()
    if not isinstance(details, dict):
        raise ValueError("Details are not a JSON object")
    return details


def _get_values(entry: dict[str, Any], details: dict[str, Any]) -> dict[str, Any]:
    text_urls, osi_url, faq_url, homepage_url = _deduplicate_urls(details)
    return {
        "scancode_key": (entry.get("license_key") or "")[:255],
        "scancode_category": (entry.get("category") or "")[:64],
        "scancode_owner": (details.get("owner") or "")[:255],
        "scancode_homepage_url": homepage_url[:2048],
        "scancode_osi_url": osi_url[:2048],
        "scancode_faq_url": faq_url[:2048],
        "scancode_text_urls": text_urls,
    }


def _deduplicate_urls(details: dict[str, Any]) -> tuple[list[str], str, str, str]:
    """
    ScanCode LicenseDB often has the same URL in several fields. Each URL is kept only in the
    most specific field, in the order license text, OSI, FAQ, homepage.
    """
    seen: set[str] = set()

    def is_new(url: str) -> bool:
        normalized_url = _normalize_url(url)
        if not normalized_url or normalized_url in seen:
            return False
        seen.add(normalized_url)
        return True

    text_urls = [url for url in details.get("text_urls") or [] if isinstance(url, str) and is_new(url)]
    single_urls = []
    for field in ("osi_url", "faq_url", "homepage_url"):
        url = details.get(field) or ""
        single_urls.append(url if is_new(url) else "")

    return text_urls, single_urls[0], single_urls[1], single_urls[2]


def _normalize_url(url: str) -> str:
    normalized_url = url.strip().lower()
    normalized_url = normalized_url.removeprefix("https://").removeprefix("http://")
    return normalized_url.rstrip("/")


def _set_values(spdx_license: License, values: dict[str, Any]) -> bool:
    changed_fields = [field for field in SCANCODE_FIELDS if getattr(spdx_license, field) != values[field]]
    if not changed_fields:
        return False

    for field in changed_fields:
        setattr(spdx_license, field, values[field])
    spdx_license.save(update_fields=changed_fields)
    return True
