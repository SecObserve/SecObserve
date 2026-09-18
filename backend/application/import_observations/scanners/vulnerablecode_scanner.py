from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from itertools import batched
from typing import Any, Optional
from urllib.parse import urlparse

import jsonpickle
import requests
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from application.commons.models import Settings
from application.import_observations.models import VulnerableCode_Cache
from application.import_observations.parsers.vulnerablecode.parser import (
    VulnerableCodeComponent,
    VulnerableCodeParser,
)
from application.import_observations.scanners.base_scanner import (
    BaseScanner,
    ScanException,
)
from application.licenses.models import License_Component

VULNERABLECODE_CACHE_BATCH_SIZE = 1000
VULNERABLECODE_REQUEST_TIMEOUT = 5 * 60
VULNERABLECODE_MAX_RETRIES = 5
VULNERABLECODE_BACKOFF_FACTOR = 1.0
VULNERABLECODE_MAX_RETRY_AFTER = 120


class VulnerableCodeRetry(Retry):
    def get_retry_after(self, response: Any) -> Optional[float]:
        # urllib3 sleeps for exactly what Retry-After says. DRF throttling reports the
        # remaining window, which can be an hour, and a scan that was started through
        # the API would block a worker for that long.
        retry_after = super().get_retry_after(response)
        return None if retry_after is None else min(retry_after, VULNERABLECODE_MAX_RETRY_AFTER)


@dataclass
class RequestPackages:
    purls: list[str]
    details: Optional[bool] = True
    ignore_qualifiers_subpath: Optional[bool] = False
    max_advisories: Optional[int] = 100
    reachability: Optional[bool] = False


@dataclass
class RequestAdvisories:
    purls: list[str]


class VulnerableCodeScanner(BaseScanner):
    def __init__(self) -> None:
        super().__init__()
        self.parser = VulnerableCodeParser()

        settings = Settings.load()
        self.base_url = settings.vulnerablecode_base_url
        self.cache_ttl_hours = settings.vulnerablecode_cache_ttl_hours
        self.headers = {
            "User-Agent": "VCIO_API_AGENT",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if settings.vulnerablecode_api_key:
            self.headers["Authorization"] = f"Token {settings.vulnerablecode_api_key}"

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        retry = VulnerableCodeRetry(
            total=VULNERABLECODE_MAX_RETRIES,
            backoff_factor=VULNERABLECODE_BACKOFF_FACTOR,
            status_forcelist=(429, 500, 502, 503, 504),
            # The packages and the advisories endpoint are POST only because the list of purls
            # is too long for a query string. They are queries and don't create anything, so
            # they are idempotent and safe to retry.
            allowed_methods=frozenset({"GET", "POST"}),
            # Let urllib3 retry the status_forcelist codes silently; the caller's
            # raise_for_status() surfaces a clear HTTPError once the retries are exhausted.
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        # The base URL is configured by an administrator and can be plain http
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _do_scan(self, license_components: list[License_Component]) -> Any:
        if not license_components:
            return []

        vulnerablecode_components: list[VulnerableCodeComponent] = []

        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        # Several components can have the same purl when they differ only in
        # qualifiers or subpath, which are not sent to VulnerableCode
        license_components_dict: dict[str, list[License_Component]] = {}
        for license_component in license_components:
            if license_component.component_purl:
                stripped_purl = self._strip_purl(license_component.component_purl)
                license_components_dict.setdefault(stripped_purl, []).append(license_component)

        cached_advisories = self._get_cached_advisories(license_components_dict.keys())
        self._append_components(vulnerablecode_components, license_components_dict, cached_advisories)

        uncached_purls = [purl for purl in license_components_dict if purl not in cached_advisories]
        if not uncached_purls:
            return vulnerablecode_components

        packages_advisories, fallback_urls = self._get_packages(uncached_purls)

        advisories_per_purl = self._get_advisories(
            license_components=license_components_dict,
            packages_advisories=packages_advisories,
            fallback_urls=fallback_urls,
        )

        self._write_cache(uncached_purls, advisories_per_purl)

        self._append_components(vulnerablecode_components, license_components_dict, advisories_per_purl)

        return vulnerablecode_components

    def _strip_purl(self, purl: str) -> str:
        # VulnerableCode matches packages by type, namespace, name and version, so everything
        # behind the version is cut off. A plain split is used instead of PackageURL, because
        # component_purl comes from an SBOM and doesn't have to be a valid purl, and because
        # the part that is kept stays the same byte for byte.
        return purl.split("?", 1)[0].split("#", 1)[0]

    def _append_components(
        self,
        vulnerablecode_components: list[VulnerableCodeComponent],
        license_components: dict[str, list[License_Component]],
        advisories_per_purl: dict[str, list[dict]],
    ) -> None:
        for purl, advisories in advisories_per_purl.items():
            for license_component in license_components[purl]:
                for advisory in advisories:
                    vulnerablecode_components.append(
                        VulnerableCodeComponent(component=license_component, advisory=advisory)
                    )

    def _get_packages(self, purls: list[str]) -> tuple[dict[str, list[dict]], dict[str, str]]:
        # If a package is affected by more than max_advisories advisories, VulnerableCode returns
        # affected_by_vulnerabilities_url instead of affected_by_vulnerabilities
        packages_advisories: dict[str, list[dict]] = {}
        fallback_urls: dict[str, str] = {}

        packages_request_data = RequestPackages(purls=purls)
        packages_url = f"{self.base_url}/api/v3/packages/"

        while packages_url:
            response = self.session.post(  # nosec B113
                # This is a false positive, there is a timeout of 5 minutes
                url=packages_url,
                headers=self.headers,
                data=jsonpickle.encode(packages_request_data, unpicklable=False),
                timeout=VULNERABLECODE_REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            packages_url = self._rebuild_url(response.json().get("next"))
            results = response.json().get("results", [])

            for result in results:
                if result.get("affected_by_vulnerabilities_url"):
                    fallback_urls[result.get("purl")] = self._rebuild_url(result.get("affected_by_vulnerabilities_url"))
                elif result.get("affected_by_vulnerabilities"):
                    packages_advisories[result.get("purl")] = result.get("affected_by_vulnerabilities")

        return packages_advisories, fallback_urls

    def _rebuild_url(self, url: Optional[str]) -> str:
        # VulnerableCode builds URLs from the scheme and host it sees, which behind a proxy
        # can be http or a host that is not reachable from SecObserve. requests turns a POST
        # into a GET when it follows the redirect to https and the API answers that with 405.
        # So only path and query of the URL are used, the instance is always the configured one.
        if not url:
            return ""

        parsed_url = urlparse(url)
        rebuilt_url = f"{self.base_url}{parsed_url.path}"
        return f"{rebuilt_url}?{parsed_url.query}" if parsed_url.query else rebuilt_url

    def _get_advisories(
        self,
        license_components: dict[str, list[License_Component]],
        packages_advisories: dict[str, list[dict]],
        fallback_urls: dict[str, str],
    ) -> dict[str, list[dict]]:
        for purl in list(packages_advisories) + list(fallback_urls):
            if purl not in license_components:
                raise ScanException(f"No license component found for purl {purl}")

        advisories_per_purl: dict[str, list[dict]] = {}

        if packages_advisories:
            # The advisories of the packages endpoint have neither severities nor references,
            # so the details of all advisories are read with one additional request
            advisory_details = self._get_advisory_details(list(packages_advisories))
            advisories_per_purl.update(self._merge_advisories(packages_advisories, advisory_details))

        for purl, fallback_url in fallback_urls.items():
            advisories_per_purl[purl] = self._get_advisories_by_url(fallback_url)

        return advisories_per_purl

    def _get_advisory_details(self, purls: list[str]) -> dict[str, dict]:
        advisory_details: dict[str, dict] = {}

        advisories_request_data = RequestAdvisories(purls=purls)
        advisories_url = f"{self.base_url}/api/v3/advisories/"

        while advisories_url:
            response = self.session.post(  # nosec B113
                # This is a false positive, there is a timeout of 5 minutes
                url=advisories_url,
                headers=self.headers,
                data=jsonpickle.encode(advisories_request_data, unpicklable=False),
                timeout=VULNERABLECODE_REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            advisories_url = self._rebuild_url(response.json().get("next"))
            results = response.json().get("results", [])

            for result in results:
                advisory_details[result.get("advisory_uid")] = result

        return advisory_details

    def _merge_advisories(
        self,
        packages_advisories: dict[str, list[dict]],
        advisory_details: dict[str, dict],
    ) -> dict[str, list[dict]]:
        advisories_per_purl: dict[str, list[dict]] = {}

        for purl, advisories in packages_advisories.items():
            merged_advisories = []
            for advisory in advisories:
                # A new dict per purl, because fixed_by_packages of the packages endpoint
                # is specific for the purl. It is kept, the details don't have it.
                merged_advisory = {**advisory, **advisory_details.get(advisory.get("advisory_uid", ""), {})}
                if not merged_advisory.get("url"):
                    merged_advisory["url"] = merged_advisory.get("resource_url")
                merged_advisories.append(merged_advisory)
            advisories_per_purl[purl] = merged_advisories

        return advisories_per_purl

    def _get_advisories_by_url(self, url: str) -> list[dict]:
        advisories: list[dict] = []
        advisories_url = url

        while advisories_url:
            response = self.session.get(  # nosec B113
                # This is a false positive, there is a timeout of 5 minutes
                url=advisories_url,
                headers=self.headers,
                timeout=VULNERABLECODE_REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            advisories_url = self._rebuild_url(response.json().get("next"))
            advisories += response.json().get("results", [])

        return advisories

    def _get_cached_advisories(self, purls: Iterable[str]) -> dict[str, list[dict]]:
        if not self.cache_ttl_hours:
            return {}

        valid_after = timezone.now() - timedelta(hours=self.cache_ttl_hours)

        cached_advisories: dict[str, list[dict]] = {}
        # Batched to stay below the parameter limits of the databases
        for purl_batch in batched(purls, VULNERABLECODE_CACHE_BATCH_SIZE):
            cache_items = VulnerableCode_Cache.objects.filter(purl__in=purl_batch, last_updated__gte=valid_after)
            for cache_item in cache_items:
                cached_advisories[cache_item.purl] = cache_item.data

        return cached_advisories

    def _write_cache(self, purls: list[str], advisories_per_purl: dict[str, list[dict]]) -> None:
        if not self.cache_ttl_hours:
            return

        # Purls without advisories are cached with an empty list, so that they
        # don't have to be requested from VulnerableCode again
        VulnerableCode_Cache.objects.bulk_create(
            [VulnerableCode_Cache(purl=purl, data=advisories_per_purl.get(purl, [])) for purl in purls],
            batch_size=VULNERABLECODE_CACHE_BATCH_SIZE,
            update_conflicts=True,
            update_fields=["data", "last_updated"],
            unique_fields=["purl"],
        )
