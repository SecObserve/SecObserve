from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from application.vex.models import VEX_Counter
from application.vex.services.vex_base import create_document_base_id


class TestCreateDocumentBaseId(TestCase):
    def test_increments_per_prefix_and_year(self):
        year = timezone.now().year

        self.assertEqual(create_document_base_id("PREFIX"), f"{year}_0001")
        self.assertEqual(create_document_base_id("PREFIX"), f"{year}_0002")
        self.assertEqual(create_document_base_id("OTHER"), f"{year}_0001")

        self.assertEqual(VEX_Counter.objects.get(document_id_prefix="PREFIX", year=year).counter, 2)
        self.assertEqual(VEX_Counter.objects.get(document_id_prefix="OTHER", year=year).counter, 1)

    def test_locks_the_counter_row(self):
        # SQLite ignores select_for_update(), so the lock that keeps concurrent
        # requests from reading the same counter cannot be exercised here;
        # assert the lock is requested instead.
        counter = VEX_Counter(document_id_prefix="PREFIX", year=2026, counter=41)
        with patch("application.vex.services.vex_base.VEX_Counter.objects") as objects:
            objects.select_for_update.return_value.get_or_create.return_value = (counter, False)

            self.assertEqual(create_document_base_id("PREFIX"), "2026_0042")

            objects.select_for_update.assert_called_once_with()
            objects.select_for_update.return_value.get_or_create.assert_called_once_with(
                document_id_prefix="PREFIX", year=timezone.now().year
            )
