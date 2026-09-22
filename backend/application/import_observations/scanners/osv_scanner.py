from dataclasses import dataclass
from datetime import datetime
from itertools import batched
from typing import Any, Optional

import jsonpickle
import requests

from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
    OSVParser,
)
from application.import_observations.scanners.base_scanner import (
    BaseScanner,
    ScanException,
)
from application.licenses.models import License_Component


@dataclass
class RequestPURL:
    purl: str


@dataclass
class RequestPackage:
    package: RequestPURL
    page_token: Optional[str]


@dataclass
class RequestQueries:
    queries: list[RequestPackage]


OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_QUERYBATCH_SIZE = 500
OSV_QUERYBATCH_TIMEOUT = 5 * 60


class OSVScanner(BaseScanner):
    def __init__(self) -> None:
        super().__init__()
        self.parser = OSVParser()
        # The same purl is used by many products, and the nightly import keeps one scanner for
        # the whole run, so OSV is asked for a purl once instead of once per product.
        self.vulnerabilities_by_purl: dict[str, tuple[OSV_Vulnerability, ...]] = {}

    def _do_scan(self, license_components: list[License_Component]) -> Any:
        # dict.fromkeys deduplicates the purls and keeps the order of the components
        missing_purls = list(
            dict.fromkeys(
                license_component.component_purl
                for license_component in license_components
                if license_component.component_purl not in self.vulnerabilities_by_purl
            )
        )
        if missing_purls:
            self._query_purls(missing_purls)

        return [
            OSV_Component(
                license_component=license_component,
                # A copy, so that a component cannot change what the cache holds for its purl
                vulnerabilities=set(self.vulnerabilities_by_purl[license_component.component_purl]),
            )
            for license_component in license_components
        ]

    def _query_purls(self, purls: list[str]) -> None:
        """Read the vulnerabilities of the given purls from OSV into the cache of this scanner."""
        vulnerabilities: dict[str, set[OSV_Vulnerability]] = {purl: set() for purl in purls}

        page_tokens: dict[str, str] = {}
        pending = purls
        while pending:
            page_tokens = self._query_purl_page(pending, page_tokens, vulnerabilities)
            pending = list(page_tokens)

        # Tuples, because CPython shares one empty tuple: most purls have no vulnerabilities at
        # all, and the cache holds every purl of the whole scan run.
        self.vulnerabilities_by_purl.update({purl: tuple(found) for purl, found in vulnerabilities.items()})

    def _query_purl_page(
        self,
        purls: list[str],
        page_tokens: dict[str, str],
        vulnerabilities: dict[str, set[OSV_Vulnerability]],
    ) -> dict[str, str]:
        results = []

        for purls_batch in batched(purls, OSV_QUERYBATCH_SIZE):
            queries = RequestQueries(
                queries=[RequestPackage(RequestPURL(purl=purl), page_tokens.get(purl)) for purl in purls_batch]
            )

            response = requests.post(  # nosec B113
                # This is a false positive, there is a timeout of 5 minutes
                url=OSV_QUERYBATCH_URL,
                data=jsonpickle.encode(queries, unpicklable=False),
                timeout=OSV_QUERYBATCH_TIMEOUT,
            )

            response.raise_for_status()
            results.extend(response.json().get("results", []))

        if len(purls) != len(results):
            raise ScanException(  # pylint: disable=broad-exception-raised
                "Number of results is different than number of components"
            )

        next_page_tokens: dict[str, str] = {}
        for purl, result in zip(purls, results):
            for vuln in result.get("vulns", []):
                vulnerabilities[purl].add(
                    OSV_Vulnerability(
                        id=vuln.get("id"),
                        modified=datetime.fromisoformat(vuln.get("modified")),
                    )
                )
            if result.get("next_page_token"):
                next_page_tokens[purl] = result.get("next_page_token")

        return next_page_tokens
