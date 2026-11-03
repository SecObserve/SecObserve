from decimal import Decimal

from application.core.queries.observation import count_active_observations_by_severity
from application.core.services.security_gate import (
    get_security_gate_condition_filter,
    resolve_security_gate_rules,
)
from application.core.types import Severity, Status
from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin

V3 = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
V3L = "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H"
V4 = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
KEV = {"default": [{"known_exploited": True}]}


class TestSecurityGateConditionFilter(ObservationFixtureMixin, BaseTestCase):
    def count(self, conditions):
        rules = resolve_security_gate_rules(conditions)
        return count_active_observations_by_severity(self.product_1, None, get_security_gate_condition_filter(rules))

    def test_non_cve_always_counts(self):
        self._observation("secret", vulnerability_id="")

        self.assertEqual(self.count(KEV)["Critical"], 1)

    def test_ghsa_only_always_counts(self):
        self._observation("ghsa", vulnerability_id="GHSA-vjh7-7g9h-fjfh")

        self.assertEqual(self.count(KEV)["Critical"], 1)

    def test_cve_without_signal_does_not_count(self):
        self._observation("plain")

        self.assertEqual(self.count(KEV)["Critical"], 0)

    def test_empty_override_counts_everything(self):
        self._observation("high-plain", severity=Severity.SEVERITY_HIGH)
        self._observation("crit-plain")

        counts = self.count({"default": [{"known_exploited": True}], "severities": {"High": []}})

        self.assertEqual((counts["Critical"], counts["High"]), (0, 1))

    def test_inherit_uses_default(self):
        self._observation("high-kev", severity=Severity.SEVERITY_HIGH, cve_found_in="CISA KEV")
        self._observation("high-plain", severity=Severity.SEVERITY_HIGH)

        self.assertEqual(self.count(KEV)["High"], 1)

    def test_known_exploited_case_insensitive(self):
        self._observation("kev", cve_found_in="cisa kev, PoC GitHub")
        self._observation("vulncheck", cve_found_in="VulnCheck KEV")

        self.assertEqual(self.count(KEV)["Critical"], 2)

    def test_exploit_tooling_and_poc_are_separate(self):
        self._observation("msf", cve_found_in="Metasploit")
        self._observation("poc", cve_found_in="PoC GitHub")

        self.assertEqual(self.count({"default": [{"exploit_tooling": True}]})["Critical"], 1)
        self.assertEqual(self.count({"default": [{"proof_of_concept": True}]})["Critical"], 1)

    def test_epss_threshold_inclusive(self):
        self._observation("at", epss=Decimal("10.000"))
        self._observation("below", epss=Decimal("9.999"))
        self._observation("none")

        self.assertEqual(self.count({"default": [{"epss_min": 10}]})["Critical"], 1)

    def test_network_vector_v3_and_v4(self):
        self._observation("v3", cvss3_vector=V3)
        self._observation("v4", cvss4_vector=V4)
        self._observation("local", cvss3_vector=V3L)

        self.assertEqual(self.count({"default": [{"network_vector": True}]})["Critical"], 2)

    def test_fix_available(self):
        self._observation("fixable", fix_available=True)
        self._observation("unfixed", fix_available=False)
        self._observation("no-component")

        self.assertEqual(self.count({"default": [{"fix_available": True}]})["Critical"], 1)

    def test_any_combines_with_or(self):
        self._observation("kev", cve_found_in="CISA KEV")
        self._observation("msf", cve_found_in="Metasploit")
        self._observation("plain")

        self.assertEqual(self.count({"default": [{"known_exploited": True, "exploit_tooling": True}]})["Critical"], 2)

    def test_all_combines_with_and(self):
        self._observation("kev-net", cve_found_in="CISA KEV", cvss3_vector=V3)
        self._observation("kev-local", cve_found_in="CISA KEV", cvss3_vector=V3L)

        conditions = {"default": [{"operator": "all", "known_exploited": True, "network_vector": True}]}
        self.assertEqual(self.count(conditions)["Critical"], 1)

    def test_two_rules_combine_with_or(self):
        self._observation("kev", cve_found_in="CISA KEV")
        self._observation("net-epss", cvss3_vector=V3, epss=Decimal("2"))
        self._observation("net-only", cvss3_vector=V3)

        conditions = {
            "default": [{"known_exploited": True}, {"operator": "all", "network_vector": True, "epss_min": 1}]
        }
        self.assertEqual(self.count(conditions)["Critical"], 2)

    def test_inactive_never_counts(self):
        self._observation("resolved", status=Status.STATUS_RESOLVED, cve_found_in="CISA KEV")

        self.assertEqual(self.count(KEV)["Critical"], 0)

    def test_prod_rollout_set(self):
        self._observation("kev", cve_found_in="CISA KEV")
        self._observation("msf", cve_found_in="Metasploit")
        self._observation("epss", epss=Decimal("12"))
        self._observation("v4", cvss4_vector=V4)
        self._observation("plain")
        self._observation("local", cvss3_vector=V3L)
        self._observation("poc", cve_found_in="PoC GitHub")

        conditions = {
            "default": [{"known_exploited": True, "exploit_tooling": True, "epss_min": 10, "network_vector": True}]
        }
        self.assertEqual(self.count(conditions)["Critical"], 4)
