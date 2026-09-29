import json
import threading
import time
from typing import Any, Callable
from unittest import skipUnless
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.test import TransactionTestCase

from application.access_control.models import User
from application.core.models import Branch, Observation, Observation_Log, Product
from application.core.services.observation_log import create_observation_log
from application.core.services.potential_duplicates import find_potential_duplicates
from application.epss.models import EPSS_Score
from application.epss.services.epss import epss_apply_observations
from application.import_observations.services.import_observations import (
    FileUploadParameters,
    file_upload_observations,
)
from application.import_observations.services.parser_registry import register_parser


@skipUnless(connection.vendor == "postgresql", "Needs the row locks of PostgreSQL")
@patch("application.import_observations.services.import_observations.find_potential_duplicates")
class TestImportObservationsLockOrder(TransactionTestCase):
    def setUp(self) -> None:
        User.objects.create(username="admin", is_superuser=True)
        register_parser("secobserve", "SecObserveParser")
        self.product = Product.objects.create(name="product")
        self.branch = Branch.objects.create(product=self.product, name="main")

    def test_concurrent_uploads_of_the_same_file(self, _) -> None:
        self._upload(["existing"])

        # The second upload logs its new observation, which saves the product, before the existing one
        errors = self._race_with_paused_upload(["existing", "new_1"], lambda: self._upload(["new_2", "existing"]))

        self.assertEqual([], errors)
        self.assertEqual(3, Observation.objects.filter(product=self.product).count())

    def test_upload_and_potential_duplicates(self, _) -> None:
        self._upload(["existing"])
        # Its potential duplicate has gone, so the next calculation resets the flag of the observation
        Observation.objects.filter(product=self.product).update(has_potential_duplicates=True)
        Product.objects.filter(pk=self.product.pk).update(has_potential_duplicates=True)

        errors = self._race_with_paused_upload(
            ["existing", "new"], lambda: find_potential_duplicates.call_local(self.product, self.branch, None)
        )

        self.assertEqual([], errors)
        self.assertFalse(Observation.objects.filter(product=self.product, has_potential_duplicates=True).exists())

    def test_upload_and_epss(self, _) -> None:
        self._upload(["CVE-2026-0001", "CVE-2026-0002"])
        EPSS_Score.objects.bulk_create(
            [EPSS_Score(cve=cve, epss_score=0.5, epss_percentile=0.5) for cve in ("CVE-2026-0001", "CVE-2026-0002")]
        )

        # The upload updates the observation with the higher id first, the EPSS task updates them by id
        errors = self._race_with_paused_upload(["CVE-2026-0002", "new", "CVE-2026-0001"], epss_apply_observations)

        self.assertEqual([], errors)
        self.assertEqual(2, Observation.objects.filter(product=self.product, epss_score=50).count())

    def _upload(self, titles: list[str]) -> None:
        observations = [{"title": title, "vulnerability_id": title, "scanner": "scanner"} for title in titles]
        data = {"format": "SecObserve", "observations": observations}
        # Like the API, which runs every request in a transaction
        with transaction.atomic():
            file_upload_observations(
                FileUploadParameters(
                    product=Product.objects.get(pk=self.product.pk),
                    branch=Branch.objects.get(pk=self.branch.pk),
                    file=ContentFile(json.dumps(data), name="file.json"),
                    service_name="",
                    docker_image_name_tag="",
                    endpoint_url="",
                    kubernetes_cluster="",
                    kubernetes_namespace="",
                    kubernetes_resource_type="",
                    kubernetes_resource_name="",
                    suppress_licenses=True,
                    sbom=False,
                )
            )

    def _race_with_paused_upload(self, titles: list[str], other: Callable[[], Any]) -> list[Exception]:
        """
        Pauses the upload of titles at its first observation log, after it has updated the observations
        in front of it, and continues it when other waits for a lock.
        """
        upload_paused = threading.Event()
        other_waits = threading.Event()
        errors: list[Exception] = []

        def pausing_create_observation_log(**kwargs: Any) -> Observation_Log:
            if threading.current_thread().name == "upload" and not upload_paused.is_set():
                upload_paused.set()
                other_waits.wait(10)
            return create_observation_log(**kwargs)

        def run(function: Callable[[], Any]) -> None:
            try:
                function()
            except Exception as e:  # pylint: disable=broad-exception-caught
                errors.append(e)
            finally:
                connection.close()

        upload = threading.Thread(target=run, args=(lambda: self._upload(titles),), name="upload")
        other_thread = threading.Thread(target=run, args=(other,))
        with patch(
            "application.import_observations.services.import_observations.create_observation_log",
            pausing_create_observation_log,
        ):
            upload.start()
            self.assertTrue(upload_paused.wait(10))
            other_thread.start()
            self._wait_for_lock_wait()
            other_waits.set()
            upload.join()
            other_thread.join()

        return errors

    def _wait_for_lock_wait(self) -> None:
        with connection.cursor() as cursor:
            for _ in range(100):
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE wait_event_type = 'Lock' AND datname = current_database()"
                )
                if cursor.fetchone()[0]:
                    return
                time.sleep(0.1)
        self.fail("Nothing waits for a lock")
