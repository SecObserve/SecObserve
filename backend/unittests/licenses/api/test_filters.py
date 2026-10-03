from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.test import override_settings

from application.commons.types import Age_Choices
from application.licenses.api.filters import (
    ConcludedLicenseFilter,
    LicenseComponentFilter,
)
from unittests.base_test_case import BaseTestCase


class TestAgeFilters(BaseTestCase):
    @override_settings(TIME_ZONE="America/New_York")
    @patch("django.utils.timezone.now")
    def test_today_starts_at_local_midnight(self, mock_now):
        # Still 2026-03-09 in TIME_ZONE, but already 2026-03-10 in UTC
        mock_now.return_value = datetime(2026, 3, 10, 2, 0, tzinfo=timezone.utc)

        for filter_class, lookup in [
            (ConcludedLicenseFilter, "last_updated__gte"),
            (LicenseComponentFilter, "last_change__gte"),
        ]:
            with self.subTest(filter_class=filter_class.__name__):
                queryset = MagicMock()
                filter_class().get_age(queryset, "age", Age_Choices.AGE_DAY)
                queryset.filter.assert_called_once_with(**{lookup: datetime(2026, 3, 9, 4, 0, tzinfo=timezone.utc)})
