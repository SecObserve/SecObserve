from django.db import migrations, transaction
from django.db.models import Exists, Max, OuterRef, Q, Subquery

from application.core.types import Assessment_Status, Observation_Log_Comment

BATCH_SIZE = 1000


def initialize_last_assessment(apps, schema_editor):
    Observation = apps.get_model("core", "Observation")
    Observation_Log = apps.get_model("core", "Observation_Log")

    # Logs of assessments by users: no rule and none of the comments the system writes.
    # The VEX statement is no criterion, because every log of an observation with a VEX statement has it.
    assessment_logs = Observation_Log.objects.filter(
        general_rule__isnull=True,
        general_rule_rego__isnull=True,
        product_rule__isnull=True,
        product_rule_rego__isnull=True,
    ).exclude(
        Q(assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED)
        | Q(comment__in=Observation_Log_Comment.FULL_TEXT_SEARCH_EXCLUDED_COMMENTS)
    )
    for prefix in Observation_Log_Comment.FULL_TEXT_SEARCH_EXCLUDED_COMMENT_PREFIXES:
        assessment_logs = assessment_logs.exclude(comment__startswith=prefix)

    ending_logs = Observation_Log.objects.filter(
        Q(assessment_status=Assessment_Status.ASSESSMENT_STATUS_REMOVED)
        | Q(comment=Observation_Log_Comment.COMMENT_RISK_ACCEPTANCE_EXPIRED)
    )

    newest_assessment = assessment_logs.filter(observation=OuterRef("pk")).order_by("-created").values("created")[:1]
    ended_later = ending_logs.filter(observation=OuterRef("pk"), created__gt=OuterRef("last_assessment"))

    assessed = Exists(assessment_logs.filter(observation=OuterRef("pk")))
    max_id = Observation.objects.aggregate(Max("id"))["id__max"] or 0

    # Fixed ranges of ids keep each batch small, searching for the next assessed ids can scan most of the table
    for start in range(0, max_id, BATCH_SIZE):
        batch = Observation.objects.filter(id__gt=start, id__lte=start + BATCH_SIZE)
        with transaction.atomic():
            batch.filter(assessed).update(last_assessment=Subquery(newest_assessment))
            batch.filter(Exists(ended_later)).update(last_assessment=None)


class Migration(migrations.Migration):
    # One transaction per batch, so that writes of an installation that is still running cannot deadlock with it
    atomic = False

    dependencies = [
        ("core", "0101_observation_last_assessment"),
    ]

    operations = [
        migrations.RunPython(
            initialize_last_assessment,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
