import threading
from dataclasses import dataclass
from datetime import datetime
from itertools import batched
from typing import Any, Optional

import jsonpickle
import requests
from packageurl import PackageURL

from application.core.models import Branch, Product
from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
    OSVParser,
    create_osv_session,
)
from application.import_observations.scanners.base_scanner import (
    BaseScanner,
    ScanException,
)
from application.licenses.models import License_Component


@dataclass(frozen=True)
class RequestPURL:
    purl: str


@dataclass(frozen=True)
class RequestNameEcosystem:
    name: str
    ecosystem: str


@dataclass
class RequestPackage:
    package: RequestPURL
    page_token: Optional[str]


@dataclass
class RequestPackageVersion:
    package: RequestNameEcosystem
    version: Optional[str]
    page_token: Optional[str]


@dataclass
class RequestQueries:
    queries: list[RequestPackage | RequestPackageVersion]


@dataclass(frozen=True)
class OSVQuery:
    package: RequestPURL | RequestNameEcosystem
    version: Optional[str] = None

    def to_request(self, page_token: Optional[str]) -> RequestPackage | RequestPackageVersion:
        if isinstance(self.package, RequestPURL):
            return RequestPackage(self.package, page_token)
        return RequestPackageVersion(self.package, self.version, page_token)


OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_QUERYBATCH_SIZE = 500
OSV_QUERYBATCH_TIMEOUT = 5 * 60
# A connection dropped mid-response is retried once, but a heavy batch that timed out is not retried
# again and again: a batch fails after about 10 minutes instead of about 30 minutes.
OSV_QUERYBATCH_READ_RETRIES = 1


_run_caches_lock = threading.Lock()
_run_caches: dict[str, dict[OSVQuery, tuple[OSV_Vulnerability, ...]]] = {}


def _get_run_cache(run_id: str) -> dict[OSVQuery, tuple[OSV_Vulnerability, ...]]:
    with _run_caches_lock:
        if run_id not in _run_caches:
            # Only the latest run is kept, a new run asks OSV again for the vulnerabilities published since
            _run_caches.clear()
            _run_caches[run_id] = {}
        return _run_caches[run_id]


def release_run_cache(run_id: str) -> None:
    with _run_caches_lock:
        _run_caches.pop(run_id, None)


class OSVScanner(BaseScanner):
    def __init__(self, run_id: Optional[str] = None) -> None:
        super().__init__()
        self.parser: OSVParser = OSVParser()
        # The same package is used by many products. The scans of a nightly run share the cache of their run
        # within the process, so OSV is asked for a package once per run instead of once per product.
        # The key is the query instead of the purl, because the query of a Linux package depends on
        # the OSV Linux distribution of the product or branch.
        self.vulnerabilities_by_query: dict[OSVQuery, tuple[OSV_Vulnerability, ...]] = (
            _get_run_cache(run_id) if run_id else {}
        )

    def _do_scan(self, license_components: list[License_Component], product: Product, branch: Optional[Branch]) -> Any:
        queries = [self._get_query(license_component, product, branch) for license_component in license_components]

        # dict.fromkeys deduplicates the queries and keeps the order of the components
        missing_queries = [query for query in dict.fromkeys(queries) if query not in self.vulnerabilities_by_query]
        if missing_queries:
            self._query_packages(missing_queries)

        return [
            OSV_Component(
                license_component=license_component,
                # A copy, so that a component cannot change what the cache holds for its query
                vulnerabilities=set(self.vulnerabilities_by_query[query]),
            )
            for license_component, query in zip(license_components, queries)
        ]

    def _get_query(self, license_component: License_Component, product: Product, branch: Optional[Branch]) -> OSVQuery:
        purl = license_component.component_purl
        try:
            parsed_purl = PackageURL.from_string(purl)
        except ValueError:
            return OSVQuery(RequestPURL(purl=purl))

        ecosystem = self.parser.get_query_osv_ecosystem(parsed_purl, product, branch)
        if ecosystem is None:
            return OSVQuery(RequestPURL(purl=purl))

        return OSVQuery(
            RequestNameEcosystem(name=parsed_purl.name, ecosystem=ecosystem),
            self.parser.get_query_version(parsed_purl),
        )

    def _query_packages(self, queries: list[OSVQuery]) -> None:
        """Read the vulnerabilities of the given queries from OSV into the cache of this scanner."""
        vulnerabilities: dict[OSVQuery, set[OSV_Vulnerability]] = {query: set() for query in queries}

        page_tokens: dict[OSVQuery, str] = {}
        pending = queries
        with create_osv_session(read_retries=OSV_QUERYBATCH_READ_RETRIES) as session:
            while pending:
                page_tokens = self._query_page(session, pending, page_tokens, vulnerabilities)
                pending = list(page_tokens)

        # Tuples, because CPython shares one empty tuple: most packages have no vulnerabilities at
        # all, and the cache holds every package of the whole scan run.
        self.vulnerabilities_by_query.update({query: tuple(found) for query, found in vulnerabilities.items()})

    def _query_page(
        self,
        session: requests.Session,
        queries: list[OSVQuery],
        page_tokens: dict[OSVQuery, str],
        vulnerabilities: dict[OSVQuery, set[OSV_Vulnerability]],
    ) -> dict[OSVQuery, str]:
        results = []

        for queries_batch in batched(queries, OSV_QUERYBATCH_SIZE):
            request_queries = RequestQueries(
                queries=[query.to_request(page_tokens.get(query)) for query in queries_batch]
            )

            response = session.post(
                url=OSV_QUERYBATCH_URL,
                data=jsonpickle.encode(request_queries, unpicklable=False),
                timeout=OSV_QUERYBATCH_TIMEOUT,
            )

            response.raise_for_status()
            results.extend(response.json().get("results", []))

        if len(queries) != len(results):
            raise ScanException(  # pylint: disable=broad-exception-raised
                "Number of results is different than number of components"
            )

        next_page_tokens: dict[OSVQuery, str] = {}
        for query, result in zip(queries, results):
            for vuln in result.get("vulns", []):
                vulnerabilities[query].add(
                    OSV_Vulnerability(
                        id=vuln.get("id"),
                        modified=datetime.fromisoformat(vuln.get("modified")),
                    )
                )
            if result.get("next_page_token"):
                next_page_tokens[query] = result.get("next_page_token")

        return next_page_tokens
