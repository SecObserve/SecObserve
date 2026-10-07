from datetime import timezone as datetime_timezone
from os import path
from unittest.mock import patch

from django.utils import timezone

from application.commons.models import Settings
from application.core.models import Observation, Product
from application.core.types import Severity
from application.epss.models import Exploit_Information
from application.epss.services.cvss_bt import (
    apply_exploit_information_observations,
    import_cvss_bt,
)
from application.import_observations.models import Parser
from application.import_observations.types import Parser_Source, Parser_Type
from unittests.base_test_case import BaseTestCase


class TestCVSS_BT(BaseTestCase):

    @patch("requests.get")
    @patch("epss.services.cvss_bt.timezone.now")
    def test_import_cvss_bt(self, mock_now, mock_requests_get) -> None:
        mock_now.return_value = timezone.datetime(2025, 1, 1, 0, 0, 0, 452618, datetime_timezone.utc)
        mock_requests_get.return_value = MockResponse()

        parser = Parser(name="Parser", type=Parser_Type.TYPE_OTHER, source=Parser_Source.SOURCE_OTHER)
        parser.save()

        product = Product(name="CVSS_BT Test")
        product.save()

        observation = Observation(
            title="too old",
            vulnerability_id="CVE-2015-0001",
            product=product,
            parser_severity=Severity.SEVERITY_UNKNOWN,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="all",
            vulnerability_id="CVE-2025-0001",
            parser_severity=Severity.SEVERITY_UNKNOWN,
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="cisa",
            vulnerability_id="CVE-2025-0002",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="vulncheck",
            vulnerability_id="CVE-2025-0003",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="exploitdb",
            vulnerability_id="CVE-2025-0004",
            product=product,
            cvss4_vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:L/SC:N/SI:N/SA:N/E:P",
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="metasploit",
            vulnerability_id="CVE-2025-0005",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="nuclei",
            vulnerability_id="CVE-2025-0006",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="poc_github",
            vulnerability_id="CVE-2025-0007",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="invalid cvss 3.1",
            vulnerability_id="CVE-2025-0008",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="invalid cvss 4.0",
            vulnerability_id="CVE-2025-0009",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        observation = Observation(
            title="no change",
            vulnerability_id="CVE-2025-0010",
            product=product,
            import_last_seen=timezone.now(),
            parser=parser,
        ).save()

        # with feature_exploit_information = True

        import_cvss_bt()

        mock_requests_get.assert_called_with(
            "https://raw.githubusercontent.com/t0sche/cvss-bt/refs/heads/main/cvss-bt.csv", timeout=300, stream=True
        )

        self.assertEqual(9, Exploit_Information.objects.count())

        observation = Observation.objects.get(title="too old")
        self.assertEqual("", observation.cve_found_in)

        observation = Observation.objects.get(title="all")
        self.assertEqual(
            "CISA KEV, Exploit-DB, Metasploit, Nuclei, PoC GitHub, VulnCheck KEV", observation.cve_found_in
        )
        self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
        self.assertEqual(7.5, observation.cvss3_score)
        self.assertEqual(Severity.SEVERITY_HIGH, observation.current_severity)

        observation = Observation.objects.get(title="cisa")
        self.assertEqual("CISA KEV", observation.cve_found_in)
        self.assertEqual(
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/E:P", observation.cvss4_vector
        )
        self.assertEqual(Severity.SEVERITY_HIGH, observation.current_severity)

        observation = Observation.objects.get(title="exploitdb")
        self.assertEqual("Exploit-DB", observation.cve_found_in)
        self.assertEqual(
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:L/SC:N/SI:N/SA:N/E:P", observation.cvss4_vector
        )

        observation = Observation.objects.get(title="metasploit")
        self.assertEqual("Metasploit", observation.cve_found_in)

        observation = Observation.objects.get(title="nuclei")
        self.assertEqual("Nuclei", observation.cve_found_in)

        observation = Observation.objects.get(title="poc_github")
        self.assertEqual("PoC GitHub", observation.cve_found_in)

        observation = Observation.objects.get(title="vulncheck")
        self.assertEqual("VulnCheck KEV", observation.cve_found_in)

        observation = Observation.objects.get(title="invalid cvss 3.1")
        self.assertEqual("CISA KEV, PoC GitHub", observation.cve_found_in)
        self.assertEqual("", observation.cvss3_vector)

        observation = Observation.objects.get(title="invalid cvss 4.0")
        self.assertEqual("Exploit-DB, VulnCheck KEV", observation.cve_found_in)
        self.assertEqual("", observation.cvss4_vector)

        observation = Observation.objects.get(title="no change")
        self.assertEqual("", observation.cve_found_in)

        # with feature_exploit_information = False

        settings = Settings.load()
        settings.feature_exploit_information = False

        apply_exploit_information_observations(settings)

        observation = Observation.objects.get(title="all")
        self.assertEqual("", observation.cve_found_in)

        observation = Observation.objects.get(title="cisa")
        self.assertEqual("", observation.cve_found_in)

        observation = Observation.objects.get(title="exploitdb")
        self.assertEqual("", observation.cve_found_in)

        observation = Observation.objects.get(title="metasploit")
        self.assertEqual("", observation.cve_found_in)

        observation = Observation.objects.get(title="nuclei")
        self.assertEqual("", observation.cve_found_in)

        observation = Observation.objects.get(title="poc_github")
        self.assertEqual("", observation.cve_found_in)

    def test_apply_exploit_information_observations_without_query_per_observation(self) -> None:
        parser = Parser(name="Parser", type=Parser_Type.TYPE_OTHER, source=Parser_Source.SOURCE_OTHER)
        parser.save()
        product = Product(name="CVSS_BT Test")
        product.save()

        for number in range(3):
            Observation(
                title=f"observation {number}",
                vulnerability_id=f"CVE-2025-010{number}",
                parser_severity=Severity.SEVERITY_UNKNOWN,
                product=product,
                import_last_seen=timezone.now(),
                parser=parser,
            ).save()
            Exploit_Information.objects.create(
                cve=f"CVE-2025-010{number}",
                base_cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                cisa_kev=True,
            )

        settings = Settings.load()

        # Observations, their exploit information, the update and the empty next batch.
        # A field missing in EXPLOIT_INFORMATION_FIELDS would add one query per observation.
        with self.assertNumQueries(4):
            num_observations = apply_exploit_information_observations(settings)

        self.assertEqual(3, num_observations)
        for observation in Observation.objects.filter(product=product):
            self.assertEqual("CISA KEV", observation.cve_found_in)
            self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
            self.assertEqual(7.5, observation.cvss3_score)
            self.assertEqual(Severity.SEVERITY_HIGH, observation.current_severity)


class MockResponse:
    def __init__(self):
        self.in_file = open(path.dirname(__file__) + "/files/cvss_bt.csv", "rb")
        self.raise_for_status_called = False

    def raise_for_status(self):
        self.raise_for_status_called = True

    def iter_lines(self):
        lines = []
        for line in self.in_file.readlines():
            lines.append(line)
        return lines
