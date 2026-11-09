from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import override_settings

from application.commons.types import Age_Choices
from application.core.api.filters import (
    ObservationFilter,
    ObservationLogFilter,
    ProductFilter,
)
from application.core.models import Observation
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


class TestAssessedFilter(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        Observation.objects.filter(pk__in=[1, 3]).update(last_assessment=datetime.now(timezone.utc))

    def test_assessed(self) -> None:
        for value, expected in [("true", [1, 3]), ("false", [2, 4])]:
            with self.subTest(assessed=value):
                observations = ObservationFilter({"assessed": value}, queryset=Observation.objects.order_by("id")).qs
                self.assertEqual(expected, [observation.pk for observation in observations])
