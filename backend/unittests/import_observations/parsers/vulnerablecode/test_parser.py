from json import loads
from unittest import skip

from application.import_observations.parsers.vulnerablecode.parser import (
    VulnerableCodeComponent,
    VulnerableCodeParser,
)
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase

CVSS3_VECTOR = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"
CVSS4_VECTOR = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:N"


class TestVulnerableCodeParser(BaseTestCase):
    def _license_component(self, **kwargs) -> License_Component:
        defaults = {
            "product": self.product_1,
            "branch": self.branch_1,
            "component_name": "django",
            "component_version": "5.1.2",
            "component_name_version": "django:5.1.2",
            "component_type": "Framework",
            "component_purl": "pkg:pypi/django@5.1.2",
            "component_purl_type": "pypi",
            "component_cpe": "cpe:/a:djangoproject:django:5.1.2",
            "component_cyclonedx_bom_link": "urn:cdx:a/1#b",
            "component_dependencies": "django_dependencies",
        }
        defaults.update(kwargs)
        return License_Component(**defaults)

    # ---------------------------------------------------------------
    # get_name / get_type
    # ---------------------------------------------------------------

    def test_get_name(self):
        self.assertEqual("VulnerableCode", VulnerableCodeParser.get_name())

    def test_get_type(self):
        self.assertEqual("SCA", VulnerableCodeParser.get_type())

    # ---------------------------------------------------------------
    # get_observations
    # ---------------------------------------------------------------

    def test_no_observations(self):
        parser = VulnerableCodeParser()
        observations, scanner = parser.get_observations([], self.product_1, self.branch_1)

        self.assertEqual("VulnerableCode", scanner)
        self.assertEqual([], observations)

    def test_get_observations_full_advisory(self):
        advisory = {
            "advisory_uid": "advisory-uid-1",
            "aliases": ["GHSA-m9g8-fxxm-xg86", "CVE-2024-53908"],
            "summary": "Potential SQL injection in HasKey lookup",
            "severities": [
                {"scoring_elements": CVSS3_VECTOR},
                {"scoring_elements": CVSS4_VECTOR},
            ],
            "fixed_by_packages": ["pkg:pypi/django@5.1.4"],
            "url": "https://public.vulnerablecode.io/api/v3/advisories/1",
            "references": [
                {"url": "https://www.djangoproject.com/weblog/2024/dec/04/security-releases/"},
                {"url": "https://nvd.nist.gov/vuln/detail/CVE-2024-53908"},
            ],
        }

        parser = VulnerableCodeParser()
        observations, scanner = parser.get_observations(
            [VulnerableCodeComponent(component=self._license_component(), advisory=advisory)],
            self.product_1,
            self.branch_1,
        )

        self.assertEqual("VulnerableCode", scanner)
        self.assertEqual(1, len(observations))

        observation = observations[0]
        self.assertEqual("CVE-2024-53908", observation.title)
        self.assertEqual("Potential SQL injection in HasKey lookup", observation.description)
        self.assertEqual("Update to version 5.1.4", observation.recommendation)
        self.assertEqual(CVSS3_VECTOR, observation.cvss3_vector)
        self.assertEqual(CVSS4_VECTOR, observation.cvss4_vector)
        self.assertEqual("CVE-2024-53908", observation.vulnerability_id)
        self.assertEqual("GHSA-m9g8-fxxm-xg86", observation.vulnerability_id_aliases)

        self.assertEqual("django", observation.origin_component_name)
        self.assertEqual("5.1.2", observation.origin_component_version)
        self.assertEqual("Framework", observation.origin_component_type)
        self.assertEqual("pkg:pypi/django@5.1.2", observation.origin_component_purl)
        self.assertEqual("cpe:/a:djangoproject:django:5.1.2", observation.origin_component_cpe)
        self.assertEqual("urn:cdx:a/1#b", observation.origin_component_cyclonedx_bom_link)
        self.assertEqual("django_dependencies", observation.origin_component_dependencies)

        self.assertEqual(
            [
                "https://public.vulnerablecode.io/api/v3/advisories/1",
                "https://www.djangoproject.com/weblog/2024/dec/04/security-releases/",
                "https://nvd.nist.gov/vuln/detail/CVE-2024-53908",
            ],
            observation.unsaved_references,
        )

        self.assertEqual(1, len(observation.unsaved_evidences))
        self.assertEqual("Advisory", observation.unsaved_evidences[0][0])
        self.assertEqual(advisory, loads(observation.unsaved_evidences[0][1]))

    def test_get_observations_multiple_components(self):
        advisory_django = {
            "aliases": ["CVE-2024-53908"],
            "summary": "Potential SQL injection in HasKey lookup",
            "url": "https://public.vulnerablecode.io/api/v3/advisories/1",
        }
        advisory_json = {
            "aliases": ["CVE-2022-45688"],
            "summary": "json stack overflow vulnerability",
            "url": "https://public.vulnerablecode.io/api/v3/advisories/2",
        }

        component_json = self._license_component(
            component_name="json",
            component_version="20190722",
            component_name_version="json:20190722",
            component_type="Library",
            component_purl="pkg:maven/org.json/json@20190722?type=jar",
            component_purl_type="maven",
            component_cpe="cpe:/a:org.json:json:20190722",
            component_cyclonedx_bom_link="urn:cdx:a/2#c",
            component_dependencies="json_dependencies",
        )

        parser = VulnerableCodeParser()
        observations, _ = parser.get_observations(
            [
                VulnerableCodeComponent(component=self._license_component(), advisory=advisory_django),
                VulnerableCodeComponent(component=component_json, advisory=advisory_json),
            ],
            self.product_1,
            self.branch_1,
        )

        self.assertEqual(2, len(observations))

        self.assertEqual("CVE-2024-53908", observations[0].title)
        self.assertEqual("django", observations[0].origin_component_name)
        self.assertEqual(["https://public.vulnerablecode.io/api/v3/advisories/1"], observations[0].unsaved_references)
        self.assertEqual(1, len(observations[0].unsaved_evidences))
        self.assertEqual(advisory_django, loads(observations[0].unsaved_evidences[0][1]))

        self.assertEqual("CVE-2022-45688", observations[1].title)
        self.assertEqual("json", observations[1].origin_component_name)
        self.assertEqual("pkg:maven/org.json/json@20190722?type=jar", observations[1].origin_component_purl)
        self.assertEqual(["https://public.vulnerablecode.io/api/v3/advisories/2"], observations[1].unsaved_references)
        self.assertEqual(1, len(observations[1].unsaved_evidences))
        self.assertEqual(advisory_json, loads(observations[1].unsaved_evidences[0][1]))

    def test_get_observations_empty_advisory(self):
        parser = VulnerableCodeParser()
        observations, _ = parser.get_observations(
            [VulnerableCodeComponent(component=self._license_component(), advisory={})],
            self.product_1,
            self.branch_1,
        )

        self.assertEqual(1, len(observations))

        observation = observations[0]
        # Without aliases there is no vulnerability id, the title is used as a fallback
        self.assertEqual("No title", observation.title)
        self.assertEqual("No title", observation.vulnerability_id)
        self.assertEqual("", observation.description)
        self.assertEqual("", observation.recommendation)
        self.assertEqual("", observation.cvss3_vector)
        self.assertEqual("", observation.cvss4_vector)
        self.assertEqual("", observation.vulnerability_id_aliases)
        self.assertEqual([], observation.unsaved_references)
        self.assertEqual({}, loads(observation.unsaved_evidences[0][1]))

    def test_get_observations_title_from_advisory_uid(self):
        advisory = {
            "advisory_uid": "pysec/PYSEC-2024-157",
            "aliases": ["CVE-2024-53908", "CVE-2024-53907"],
            "summary": "Potential SQL injection in HasKey lookup",
        }

        parser = VulnerableCodeParser()
        observations, _ = parser.get_observations(
            [VulnerableCodeComponent(component=self._license_component(), advisory=advisory)],
            self.product_1,
            self.branch_1,
        )

        observation = observations[0]
        # Two CVE aliases are ambiguous, so the title falls back to the advisory_uid segment
        self.assertEqual("PYSEC-2024-157", observation.title)
        self.assertEqual("PYSEC-2024-157", observation.vulnerability_id)
        # The title matches no alias, so every alias is kept
        self.assertEqual("CVE-2024-53908, CVE-2024-53907", observation.vulnerability_id_aliases)

    # ---------------------------------------------------------------
    # _get_title
    # ---------------------------------------------------------------

    def test_get_title_no_aliases(self):
        self.assertEqual("No title", VulnerableCodeParser()._get_title({}))

    def test_get_title_single_alias(self):
        self.assertEqual("GHSA-m9g8-fxxm-xg86", VulnerableCodeParser()._get_title({"aliases": ["GHSA-m9g8-fxxm-xg86"]}))

    def test_get_title_cve_wins_over_other_alias(self):
        advisory = {"aliases": ["GHSA-m9g8-fxxm-xg86", "CVE-2024-53908"]}
        self.assertEqual("CVE-2024-53908", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_other_alias_does_not_override_cve(self):
        advisory = {"aliases": ["CVE-2024-53908", "GHSA-m9g8-fxxm-xg86"]}
        self.assertEqual("CVE-2024-53908", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_multiple_cves_uses_first_alias(self):
        # More than one CVE alias is ambiguous, so no CVE is picked and the first alias is used
        advisory = {"aliases": ["CVE-2024-53908", "CVE-2024-53907"]}
        self.assertEqual("CVE-2024-53908", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_from_advisory_uid(self):
        advisory = {"advisory_uid": "pysec/PYSEC-2024-157"}
        self.assertEqual("PYSEC-2024-157", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_from_advisory_uid_multiple_slashes(self):
        advisory = {"advisory_uid": "vulnerablecode/ghsa/GHSA-m9g8-fxxm-xg86"}
        self.assertEqual("GHSA-m9g8-fxxm-xg86", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_advisory_uid_without_slash_ignored(self):
        advisory = {"advisory_uid": "VCID-1234", "aliases": ["GHSA-m9g8-fxxm-xg86"]}
        self.assertEqual("GHSA-m9g8-fxxm-xg86", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_advisory_uid_without_slash_and_no_aliases(self):
        self.assertEqual("No title", VulnerableCodeParser()._get_title({"advisory_uid": "VCID-1234"}))

    def test_get_title_single_cve_replaces_advisory_uid(self):
        advisory = {"advisory_uid": "pysec/PYSEC-2024-157", "aliases": ["CVE-2024-53908"]}
        self.assertEqual("CVE-2024-53908", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_advisory_uid_wins_over_multiple_cves(self):
        advisory = {"advisory_uid": "pysec/PYSEC-2024-157", "aliases": ["CVE-2024-53908", "CVE-2024-53907"]}
        self.assertEqual("PYSEC-2024-157", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_advisory_uid_trailing_slash(self):
        advisory = {"advisory_uid": "pysec/", "aliases": ["GHSA-m9g8-fxxm-xg86"]}
        self.assertEqual("GHSA-m9g8-fxxm-xg86", VulnerableCodeParser()._get_title(advisory))

    def test_get_title_advisory_uid_none(self):
        self.assertEqual("No title", VulnerableCodeParser()._get_title({"advisory_uid": None}))

    # ---------------------------------------------------------------
    # _get_aliases
    # ---------------------------------------------------------------

    def test_get_aliases_no_aliases(self):
        self.assertEqual("", VulnerableCodeParser()._get_aliases({}, "No title"))

    def test_get_aliases_only_title(self):
        advisory = {"aliases": ["CVE-2024-53908"]}
        self.assertEqual("", VulnerableCodeParser()._get_aliases(advisory, "CVE-2024-53908"))

    def test_get_aliases_without_title(self):
        advisory = {"aliases": ["GHSA-m9g8-fxxm-xg86", "CVE-2024-53908"]}
        self.assertEqual("GHSA-m9g8-fxxm-xg86", VulnerableCodeParser()._get_aliases(advisory, "CVE-2024-53908"))

    def test_get_aliases_multiple(self):
        advisory = {"aliases": ["GHSA-m9g8-fxxm-xg86", "PYSEC-2024-157", "CVE-2024-53908"]}
        self.assertEqual(
            "GHSA-m9g8-fxxm-xg86, PYSEC-2024-157",
            VulnerableCodeParser()._get_aliases(advisory, "CVE-2024-53908"),
        )

    # ---------------------------------------------------------------
    # _get_severities
    # ---------------------------------------------------------------

    def test_get_severities_no_severities(self):
        self.assertEqual(("", ""), VulnerableCodeParser()._get_severities({}))

    def test_get_severities_cvss3_only(self):
        advisory = {"severities": [{"scoring_elements": CVSS3_VECTOR}]}
        self.assertEqual((CVSS3_VECTOR, ""), VulnerableCodeParser()._get_severities(advisory))

    def test_get_severities_cvss4_only(self):
        advisory = {"severities": [{"scoring_elements": CVSS4_VECTOR}]}
        self.assertEqual(("", CVSS4_VECTOR), VulnerableCodeParser()._get_severities(advisory))

    def test_get_severities_cvss3_and_cvss4(self):
        advisory = {"severities": [{"scoring_elements": CVSS4_VECTOR}, {"scoring_elements": CVSS3_VECTOR}]}
        self.assertEqual((CVSS3_VECTOR, CVSS4_VECTOR), VulnerableCodeParser()._get_severities(advisory))

    def test_get_severities_first_cvss3_wins(self):
        other_vector = "CVSS:3.0/AV:L/AC:H/PR:H/UI:R/S:C/C:H/I:H/A:H"
        advisory = {"severities": [{"scoring_elements": CVSS3_VECTOR}, {"scoring_elements": other_vector}]}
        self.assertEqual((CVSS3_VECTOR, ""), VulnerableCodeParser()._get_severities(advisory))

    def test_get_severities_non_cvss_ignored(self):
        advisory = {"severities": [{"scoring_elements": "7.5"}]}
        self.assertEqual(("", ""), VulnerableCodeParser()._get_severities(advisory))

    def test_get_severities_without_scoring_elements(self):
        advisory = {"severities": [{"system": "cvssv3", "value": "7.5"}]}
        self.assertEqual(("", ""), VulnerableCodeParser()._get_severities(advisory))

    # ---------------------------------------------------------------
    # _get_recommendation
    # ---------------------------------------------------------------

    def test_get_recommendation_no_fixed_by_packages(self):
        self.assertEqual("", VulnerableCodeParser()._get_recommendation({}))

    def test_get_recommendation_fixed_by_packages_not_a_list(self):
        self.assertEqual("", VulnerableCodeParser()._get_recommendation({"fixed_by_packages": None}))

    def test_get_recommendation_single_version(self):
        advisory = {"fixed_by_packages": ["pkg:pypi/django@5.1.4"]}
        self.assertEqual("Update to version 5.1.4", VulnerableCodeParser()._get_recommendation(advisory))

    def test_get_recommendation_multiple_versions(self):
        advisory = {"fixed_by_packages": ["pkg:pypi/django@5.1.4", "pkg:pypi/django@4.2.17"]}
        self.assertEqual("Update to versions 5.1.4, 4.2.17", VulnerableCodeParser()._get_recommendation(advisory))

    def test_get_recommendation_purl_without_version(self):
        advisory = {"fixed_by_packages": ["pkg:pypi/django"]}
        self.assertEqual("Update to version `pkg:pypi/django`", VulnerableCodeParser()._get_recommendation(advisory))

    def test_get_recommendation_invalid_purl(self):
        advisory = {"fixed_by_packages": ["not-a-purl"]}
        self.assertEqual("Update to version `not-a-purl`", VulnerableCodeParser()._get_recommendation(advisory))

    # ---------------------------------------------------------------
    # _get_references
    # ---------------------------------------------------------------

    def test_get_references_none(self):
        self.assertEqual([], VulnerableCodeParser()._get_references({}))

    def test_get_references_advisory_url_only(self):
        advisory = {"url": "https://public.vulnerablecode.io/api/v3/advisories/1"}
        self.assertEqual(
            ["https://public.vulnerablecode.io/api/v3/advisories/1"],
            VulnerableCodeParser()._get_references(advisory),
        )

    def test_get_references_references_only(self):
        advisory = {"references": [{"url": "https://example.com/a"}, {"url": "https://example.com/b"}]}
        self.assertEqual(
            ["https://example.com/a", "https://example.com/b"],
            VulnerableCodeParser()._get_references(advisory),
        )

    def test_get_references_advisory_url_first(self):
        advisory = {
            "url": "https://public.vulnerablecode.io/api/v3/advisories/1",
            "references": [{"url": "https://example.com/a"}],
        }
        self.assertEqual(
            ["https://public.vulnerablecode.io/api/v3/advisories/1", "https://example.com/a"],
            VulnerableCodeParser()._get_references(advisory),
        )

    def test_get_references_without_url_skipped(self):
        advisory = {"references": [{"reference_id": "GHSA-1"}, {"url": ""}, {"url": "https://example.com/a"}]}
        self.assertEqual(["https://example.com/a"], VulnerableCodeParser()._get_references(advisory))
