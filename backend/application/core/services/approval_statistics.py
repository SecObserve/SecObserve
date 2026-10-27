from typing import Any

from django.db.models.query import QuerySet

from application.core.types import Assessment_Status

COUNTERS = {
    Assessment_Status.ASSESSMENT_STATUS_APPROVED: "approved",
    Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS: "approved_with_edits",
    Assessment_Status.ASSESSMENT_STATUS_REJECTED: "rejected",
}


def get_approval_statistics(observation_logs: QuerySet) -> list[dict[str, Any]]:
    statistics: dict[int, dict[str, Any]] = {}
    seconds: dict[int, float] = {}
    # ponytail: aggregated in Python, the average of a duration is not portable to MySQL; move to SQL if it gets slow
    rows = (
        observation_logs.filter(assessment_status__in=COUNTERS)
        .order_by()
        .values_list("approval_user", "approval_user__full_name", "assessment_status", "created", "approval_date")
        .iterator(chunk_size=2000)
    )
    for approver, full_name, assessment_status, created, approval_date in rows:
        entry = statistics.setdefault(
            approver,
            {
                "approval_user": approver,
                "approval_user_full_name": full_name,
                "approved": 0,
                "approved_with_edits": 0,
                "rejected": 0,
                "total": 0,
            },
        )
        entry[COUNTERS[assessment_status]] += 1
        entry["total"] += 1
        seconds[approver] = seconds.get(approver, 0.0) + (approval_date - created).total_seconds()

    for approver, entry in statistics.items():
        entry["average_decision_hours"] = round(seconds[approver] / entry["total"] / 3600, 1)

    return sorted(statistics.values(), key=lambda entry: entry["approval_user_full_name"] or "")
