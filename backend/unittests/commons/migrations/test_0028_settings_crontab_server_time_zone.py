from importlib import import_module

from django.apps import apps
from django.test import override_settings

from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase

migration = import_module("application.commons.migrations.0028_settings_crontab_server_time_zone")


class TestShiftCrontab(BaseTestCase):
    def test_shift_crontab(self):
        self.assertEqual((10, 0), migration.shift_crontab(3, 0, 7 * 60))
        self.assertEqual((2, 15), migration.shift_crontab(20, 45, 5 * 60 + 30))
        self.assertEqual((20, 45), migration.shift_crontab(2, 15, -(5 * 60 + 30)))
        self.assertEqual((16, 0), migration.shift_crontab(1, 30, -(9 * 60 + 30)))
        self.assertEqual((1, 30), migration.shift_crontab(1, 30, 0))


class TestSettingsCrontabServerTimeZone(BaseTestCase):
    def setUp(self):
        Settings.objects.all().delete()
        Settings(
            background_epss_import_crontab_hour=3,
            background_epss_import_crontab_minute=0,
            branch_housekeeping_crontab_hour=2,
            branch_housekeeping_crontab_minute=0,
            risk_acceptance_expiry_crontab_hour=1,
            risk_acceptance_expiry_crontab_minute=0,
            api_import_crontab_hour=20,
            api_import_crontab_minute=45,
            license_import_crontab_hour=1,
            license_import_crontab_minute=30,
        ).save()

    def _crontabs(self) -> list[tuple[int, int]]:
        settings = Settings.objects.get()
        return [
            (getattr(settings, f"{crontab}_crontab_hour"), getattr(settings, f"{crontab}_crontab_minute"))
            for crontab in migration.CRONTABS
        ]

    @override_settings(TIME_ZONE="Asia/Kolkata")
    def test_forward_and_reverse(self):
        migration.crontabs_from_utc_to_server_time_zone(apps, None)
        self.assertEqual([(8, 30), (7, 30), (6, 30), (2, 15), (7, 0)], self._crontabs())

        migration.crontabs_from_server_time_zone_to_utc(apps, None)
        self.assertEqual([(3, 0), (2, 0), (1, 0), (20, 45), (1, 30)], self._crontabs())

    @override_settings(TIME_ZONE="UTC")
    def test_utc_unchanged(self):
        migration.crontabs_from_utc_to_server_time_zone(apps, None)
        self.assertEqual([(3, 0), (2, 0), (1, 0), (20, 45), (1, 30)], self._crontabs())
