from datetime import timedelta
from datetime import timezone as datetime_timezone
from os import path
from unittest.mock import patch

from django.utils import timezone

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import Observation, Observation_Log, Product
from application.core.types import Observation_Log_Comment, Severity
from application.epss.models import Exploit_Information
from application.epss.services.cvss_bt import (
    apply_exploit_information_observations,
    import_cvss_bt,
)
from application.import_observations.models import Parser
from application.import_observations.types import Parser_Source, Parser_Type
from unittests.base_test_case import BaseTestCase


class TestCVSS_BT(BaseTestCase):
    def setUp(self) -> None:
        # Observation logs written by the background job fall back to the first superuser
        User.objects.create(username="cvss_bt_superuser", is_superuser=True)
        super().setUp()

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

        _, changed = import_cvss_bt()

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

        self.assertEqual(
            set(
                Observation.objects.filter(product=product)
                .exclude(title__in=["too old", "no change"])
                .values_list("pk", flat=True)
            ),
            set(changed),
        )

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

    @patch("application.epss.services.cvss_bt.requests.get")
    def test_import_cvss_bt_invalid_first_row_returns_no_pks(self, mock_requests_get) -> None:
        mock_requests_get.return_value.iter_lines.return_value = [b"cve,epss"]

        with self.assertLogs("secobserve.epss", level="ERROR"):
            result = import_cvss_bt()

        self.assertEqual(("Error: First row of cvss-bt CSV is not valid.", []), result)

    def test_apply_exploit_information_observations_without_query_per_observation(self) -> None:
        parser = Parser(name="Parser", type=Parser_Type.TYPE_OTHER, source=Parser_Source.SOURCE_OTHER)
        parser.save()
        product = Product(name="CVSS_BT Test")
        product.save()

        for number in range(3):
            Observation(
                title=f"observation {number}",
                vulnerability_id=f"CVE-2025-010{number}",
                # A changed severity writes an observation log, which needs queries per observation
                parser_severity=Severity.SEVERITY_HIGH,
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

        # Observations, their exploit information, the update, the change timestamp of the products and the
        # empty next batch. A field missing in EXPLOIT_INFORMATION_FIELDS would add one query per observation.
        with self.assertNumQueries(5):
            changed = apply_exploit_information_observations(settings)

        self.assertEqual(sorted(Observation.objects.filter(product=product).values_list("pk", flat=True)), changed)
        for observation in Observation.objects.filter(product=product):
            self.assertEqual("CISA KEV", observation.cve_found_in)
            self.assertEqual("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H", observation.cvss3_vector)
            self.assertEqual(7.5, observation.cvss3_score)
            self.assertEqual(Severity.SEVERITY_HIGH, observation.current_severity)
            self.assertEqual(Severity.NUMERICAL_SEVERITIES[Severity.SEVERITY_HIGH], observation.numerical_severity)

    def test_apply_exploit_information_observations_marks_products_as_changed(self) -> None:
        parser = Parser.objects.create(name="Parser", type=Parser_Type.TYPE_OTHER, source=Parser_Source.SOURCE_OTHER)
        product_changed = Product.objects.create(name="changed")
        product_unchanged = Product.objects.create(name="unchanged")
        for product, cve in ((product_changed, "CVE-2025-0001"), (product_unchanged, "CVE-2025-0002")):
            Observation.objects.create(
                title=cve,
                vulnerability_id=cve,
                parser_severity=Severity.SEVERITY_UNKNOWN,
                product=product,
                import_last_seen=timezone.now(),
                parser=parser,
            )
        Exploit_Information.objects.create(
            cve="CVE-2025-0001", base_cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        )
        last_change = timezone.now() - timedelta(days=1)
        Product.objects.update(last_observation_change=last_change)
        settings = Settings.load()
        settings.feature_exploit_information = True

        apply_exploit_information_observations(settings)

        self.assertEqual(Severity.SEVERITY_CRITICAL, Observation.objects.get(title="CVE-2025-0001").current_severity)
        product_changed.refresh_from_db()
        self.assertGreater(product_changed.last_observation_change, last_change)
        product_unchanged.refresh_from_db()
        self.assertEqual(last_change, product_unchanged.last_observation_change)

    def test_apply_exploit_information_observations_only_without_cvss_vector(self) -> None:
        parser = Parser.objects.create(name="Parser", type=Parser_Type.TYPE_OTHER, source=Parser_Source.SOURCE_OTHER)
        product = Product.objects.create(name="CVSS_BT Test")
        cvss3_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        cvss4_vector = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N"
        # The observation has one CVSS version, cvss-bt has the other one
        for cve, observation_vectors, exploit_vector in (
            ("CVE-2025-0001", {"cvss4_vector": cvss4_vector}, cvss3_vector),
            ("CVE-2025-0002", {"cvss3_vector": cvss3_vector}, cvss4_vector),
        ):
            Observation.objects.create(
                title=cve,
                vulnerability_id=cve,
                product=product,
                import_last_seen=timezone.now(),
                parser=parser,
                **observation_vectors,
            )
            Exploit_Information.objects.create(cve=cve, base_cvss_vector=exploit_vector, cisa_kev=True)

        apply_exploit_information_observations(Settings.load())

        observation = Observation.objects.get(title="CVE-2025-0001")
        self.assertEqual("CISA KEV", observation.cve_found_in)
        self.assertEqual("", observation.cvss3_vector)
        self.assertEqual(cvss4_vector, observation.cvss4_vector)
        observation = Observation.objects.get(title="CVE-2025-0002")
        self.assertEqual("CISA KEV", observation.cve_found_in)
        self.assertEqual(cvss3_vector, observation.cvss3_vector)
        self.assertEqual("", observation.cvss4_vector)

    def test_apply_exploit_information_observations_log_for_changed_severity(self) -> None:
        parser = Parser.objects.create(name="Parser", type=Parser_Type.TYPE_OTHER, source=Parser_Source.SOURCE_OTHER)
        product = Product.objects.create(name="CVSS_BT Test")
        for cve, parser_severity in (
            ("CVE-2025-0001", Severity.SEVERITY_UNKNOWN),
            ("CVE-2025-0002", Severity.SEVERITY_LOW),
        ):
            Observation.objects.create(
                title=cve,
                vulnerability_id=cve,
                parser_severity=parser_severity,
                product=product,
                import_last_seen=timezone.now(),
                parser=parser,
            )
            Exploit_Information.objects.create(
                cve=cve, base_cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", cisa_kev=True
            )
        Observation_Log.objects.filter(observation__product=product).delete()

        apply_exploit_information_observations(Settings.load())

        observation = Observation.objects.get(title="CVE-2025-0001")
        self.assertEqual(
            [(Observation_Log_Comment.COMMENT_CVSS_UPDATED_BY_CVSS_BT, Severity.SEVERITY_CRITICAL)],
            list(observation.observation_logs.values_list("comment", "severity")),
        )
        self.assertEqual(observation.observation_logs.get().created, observation.last_observation_log)
        observation = Observation.objects.get(title="CVE-2025-0002")
        self.assertEqual("CISA KEV", observation.cve_found_in)
        self.assertFalse(observation.observation_logs.exists())


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
