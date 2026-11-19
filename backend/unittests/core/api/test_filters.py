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
from application.core.models import Observation, Observation_Log
from application.core.types import Assessment_Status
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


class TestLastAssessmentStatusFilter(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        # A later log of an import does not hide the assessment that needs approval
        self._create_log(1, Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL, 1)
        self._create_log(1, Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED, 2)

        # A propagated assessment replaces the rejected one
        self._create_log(2, Assessment_Status.ASSESSMENT_STATUS_REJECTED, 1)
        source = self._create_log(3, Assessment_Status.ASSESSMENT_STATUS_APPROVED, 2)
        self._create_log(2, Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED, 3, propagated_from=source)

        # The same creation time is decided by the id
        self._create_log(3, Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS, 2)
        self._create_log(3, Assessment_Status.ASSESSMENT_STATUS_APPROVED, 2)

        self._create_log(4, Assessment_Status.ASSESSMENT_STATUS_APPROVED, 1)
        self._create_log(4, Assessment_Status.ASSESSMENT_STATUS_REMOVED, 2)

    def _create_log(
        self,
        observation_id: int,
        assessment_status: str,
        minute: int,
        propagated_from: Observation_Log | None = None,
    ) -> Observation_Log:
        observation_log = Observation_Log.objects.create(
            observation_id=observation_id,
            user_id=2,
            comment="comment",
            assessment_status=assessment_status,
            propagated_from=propagated_from,
        )
        # created is set automatically when the log is created
        Observation_Log.objects.filter(pk=observation_log.pk).update(
            created=datetime(2026, 3, 10, 12, minute, tzinfo=timezone.utc)
        )
        return observation_log

    def test_last_assessment_status(self) -> None:
        for value, expected in [
            (Assessment_Status.ASSESSMENT_STATUS_APPROVED, [3]),
            (Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS, []),
            (Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL, [1]),
            (Assessment_Status.ASSESSMENT_STATUS_REJECTED, []),
            (Assessment_Status.ASSESSMENT_STATUS_REMOVED, [4]),
        ]:
            with self.subTest(last_assessment_status=value):
                observations = ObservationFilter(
                    {"last_assessment_status": value}, queryset=Observation.objects.order_by("id")
                ).qs
                self.assertEqual(expected, [observation.pk for observation in observations])

    def test_auto_approved_is_not_offered(self) -> None:
        observation_filter = ObservationFilter(
            {"last_assessment_status": Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED},
            queryset=Observation.objects.all(),
        )
        self.assertFalse(observation_filter.is_valid())
