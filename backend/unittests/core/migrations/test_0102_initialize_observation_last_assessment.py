from datetime import datetime, timedelta
from importlib import import_module
from typing import Optional
from unittest.mock import patch

from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from application.access_control.models import User
from application.core.models import Observation, Observation_Log, Product
from application.core.types import Assessment_Status, Observation_Log_Comment, Status
from application.import_observations.models import Parser
from application.import_observations.types import Parser_Source, Parser_Type

migration = import_module("application.core.migrations.0102_initialize_observation_last_assessment")


class TestInitializeLastAssessment(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="user_last_assessment")
        self.product = Product.objects.create(name="product")
        self.parser = Parser.objects.create(name="parser", type=Parser_Type.TYPE_SCA, source=Parser_Source.SOURCE_FILE)
        self.start = timezone.now() - timedelta(days=10)

    def _create_observation(self, title: str) -> Observation:
        return Observation.objects.create(
            title=title,
            product=self.product,
            parser=self.parser,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

    def _log(
        self,
        observation: Observation,
        day: int,
        comment: str,
        assessment_status: str = Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
    ) -> datetime:
        observation_log = Observation_Log.objects.create(
            observation=observation, user=self.user, comment=comment, assessment_status=assessment_status
        )
        created = self.start + timedelta(days=day)
        Observation_Log.objects.filter(pk=observation_log.pk).update(created=created)
        return created

    def _last_assessment(self, observation: Observation) -> Optional[datetime]:
        observation.refresh_from_db()
        return observation.last_assessment

    def test_initialize_last_assessment(self) -> None:
        not_assessed = self._create_observation("not_assessed")
        self._log(not_assessed, 0, Observation_Log_Comment.COMMENT_SET_BY_PARSER)
        self._log(not_assessed, 1, f"{Observation_Log_Comment.COMMENT_PREFIX_UPDATED_BY_GENERAL_RULE}rule")

        assessed = self._create_observation("assessed")
        self._log(assessed, 0, Observation_Log_Comment.COMMENT_SET_BY_PARSER)
        self._log(assessed, 1, "first look")
        pending_at = self._log(assessed, 2, "not exploitable", Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL)
        self._log(assessed, 3, f"{Observation_Log_Comment.COMMENT_PREFIX_UPDATED_BY_PRODUCT_RULE}rule")

        removed = self._create_observation("removed")
        self._log(removed, 1, "false positive")
        self._log(removed, 2, "not a false positive", Assessment_Status.ASSESSMENT_STATUS_REMOVED)

        reassessed = self._create_observation("reassessed")
        self._log(reassessed, 1, "false positive")
        self._log(reassessed, 2, "not a false positive", Assessment_Status.ASSESSMENT_STATUS_REMOVED)
        reassessed_at = self._log(reassessed, 3, "false positive after all")

        expired = self._create_observation("expired")
        self._log(expired, 1, "accepted")
        self._log(expired, 2, Observation_Log_Comment.COMMENT_RISK_ACCEPTANCE_EXPIRED)

        # More observations than the batch size, so that the batching is used
        with patch.object(migration, "BATCH_SIZE", 2):
            migration.initialize_last_assessment(apps, None)

        self.assertIsNone(self._last_assessment(not_assessed))
        self.assertEqual(pending_at, self._last_assessment(assessed))
        self.assertIsNone(self._last_assessment(removed))
        self.assertEqual(reassessed_at, self._last_assessment(reassessed))
        self.assertIsNone(self._last_assessment(expired))

    def test_migration_is_not_atomic(self) -> None:
        # One transaction per batch is what keeps the migration from deadlocking with a running installation
        self.assertFalse(migration.Migration.atomic)
