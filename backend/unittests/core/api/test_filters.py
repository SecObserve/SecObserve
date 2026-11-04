from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import override_settings

from application.access_control.models import User
from application.commons.types import Age_Choices
from application.core.api.filters import (
    ObservationFilter,
    ObservationLogFilter,
    ProductFilter,
)
from application.core.models import Observation, Observation_Log
from unittests.base_test_case import BaseTestCase


class TestAgeFilters(BaseTestCase):
    @override_settings(TIME_ZONE="Asia/Ho_Chi_Minh")
    @patch("django.utils.timezone.now")
    def test_today_starts_at_local_midnight(self, mock_now):
        # 2026-03-11 03:00 in TIME_ZONE, but still 2026-03-10 in UTC
        mock_now.return_value = datetime(2026, 3, 10, 20, 0, tzinfo=timezone.utc)

        for filter_class, lookup in [
            (ProductFilter, "last_observation_change__gte"),
            (ObservationFilter, "last_observation_log__gte"),
            (ObservationLogFilter, "created__gte"),
        ]:
            with self.subTest(filter_class=filter_class.__name__):
                queryset = MagicMock()
                filter_class().get_age(queryset, "age", Age_Choices.AGE_DAY)
                queryset.filter.assert_called_once_with(**{lookup: datetime(2026, 3, 10, 17, 0, tzinfo=timezone.utc)})


class TestExpiryFilters(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        Observation.objects.filter(pk=3).update(risk_acceptance_expiry_date=date(2030, 1, 1))
        Observation.objects.filter(pk=4).update(risk_acceptance_expiry_date=date(2030, 6, 1))

    def test_observation_expiry_date_before(self):
        observations = ObservationFilter(
            {"risk_acceptance_expiry_date_before": "2030-03-01"}, queryset=Observation.objects.all()
        ).qs
        self.assertEqual([3], [observation.pk for observation in observations])

    def test_observation_log_expiry_extension(self):
        log = {"observation": Observation.objects.get(pk=4), "user": User.objects.get(pk=1)}
        extension = Observation_Log.objects.create(
            **log, comment="extension", risk_acceptance_expiry_date=date(2031, 1, 1)
        )
        Observation_Log.objects.create(
            **log, status="Risk accepted", comment="assessment", risk_acceptance_expiry_date=date(2031, 1, 1)
        )

        logs = ObservationLogFilter({"expiry_extension": "true"}, queryset=Observation_Log.objects.all()).qs
        self.assertEqual([extension.pk], [log.pk for log in logs])
        logs = ObservationLogFilter({"expiry_extension": "false"}, queryset=Observation_Log.objects.all()).qs
        self.assertNotIn(extension.pk, [log.pk for log in logs])
