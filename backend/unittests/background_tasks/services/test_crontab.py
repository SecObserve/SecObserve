from datetime import datetime

from django.test import SimpleTestCase, override_settings

from application.background_tasks.services.crontab import crontab_in_time_zone


class TestCrontabInTimeZone(SimpleTestCase):
    def test_utc_by_default(self):
        validate = crontab_in_time_zone(minute=30, hour=3)

        self.assertTrue(validate(datetime(2026, 10, 8, 3, 30)))
        self.assertFalse(validate(datetime(2026, 10, 8, 4, 30)))

    @override_settings(BACKGROUND_TASKS_TIME_ZONE="Asia/Ho_Chi_Minh")
    def test_hour_in_time_zone(self):
        validate = crontab_in_time_zone(minute=0, hour=3)

        # 03:00 in Ho Chi Minh City is 20:00 UTC of the day before
        self.assertTrue(validate(datetime(2026, 10, 7, 20, 0)))
        self.assertFalse(validate(datetime(2026, 10, 8, 3, 0)))

    @override_settings(BACKGROUND_TASKS_TIME_ZONE="Europe/Berlin")
    def test_daylight_saving_time(self):
        validate = crontab_in_time_zone(minute=0, hour=3)

        self.assertTrue(validate(datetime(2026, 1, 15, 2, 0)))
        self.assertTrue(validate(datetime(2026, 7, 15, 1, 0)))
