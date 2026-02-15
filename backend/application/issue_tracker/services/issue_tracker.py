from typing import Optional

from huey.contrib.djhuey import db_task, task

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.core.models import Observation, Product
from application.core.types import Severity, Status
from application.issue_tracker.issue_trackers.base_issue_tracker import (
    BaseIssueTracker,
    Issue,
)
from application.issue_tracker.issue_trackers.github_issue_tracker import (
    GitHubIssueTracker,
)
from application.issue_tracker.issue_trackers.gitlab_issue_tracker import (
    GitLabIssueTracker,
)
from application.issue_tracker.issue_trackers.jira_issue_tracker import JiraIssueTracker
from application.issue_tracker.types import Issue_Tracker
from application.notifications.services.tasks import handle_task_exception


def push_observations_to_issue_tracker(product: Product, observations: set[Observation]) -> None:
    if product.issue_tracker_active:
        for observation in observations:
            push_observation_to_issue_tracker(observation, get_current_user())


@db_task()
def push_observation_to_issue_tracker(observation: Observation, user: User) -> None:
    try:
        if (
            observation.product.issue_tracker_active
            and observation.branch == observation.product.repository_default_branch
        ):
            issue_tracker = issue_tracker_factory(observation.product)
            issue = _get_issue(observation, issue_tracker)

            # If the issue_tracker_issue_id is set but the issue does not exist, remove the id
            if observation.issue_tracker_issue_id and not issue:
                observation.issue_tracker_issue_id = ""
                observation.save()

            if observation.current_status in Status.STATUS_ACTIVE:
                if observation.product.issue_tracker_minimum_severity:
                    numerical_minimum_severity = Severity.NUMERICAL_SEVERITIES.get(
                        observation.product.issue_tracker_minimum_severity, 99
                    )
                else:
                    numerical_minimum_severity = 99

                if observation.numerical_severity <= numerical_minimum_severity:
                    if issue:
                        issue_tracker.update_issue(observation, issue)
                    else:
                        issue_id = issue_tracker.create_issue(observation)
                        observation.issue_tracker_issue_id = issue_id
                        observation.save()
                else:
                    if issue and not observation.issue_tracker_issue_closed:
                        issue_tracker.close_issue(observation, issue)
                        observation.issue_tracker_issue_closed = True
                        observation.save()
            else:
                if issue:
                    issue_tracker.close_issue(observation, issue)
                    observation.issue_tracker_issue_closed = True
                    observation.save()
    except Exception as e:
        handle_task_exception(e, user)


@task()
def push_deleted_observation_to_issue_tracker(product: Product, issue_id: Optional[str], user: User) -> None:
    try:
        if product.issue_tracker_active and issue_id:
            issue_tracker = issue_tracker_factory(product)
            issue = issue_tracker.get_issue(product, issue_id)
            if issue:
                issue_tracker.close_issue_for_deleted_observation(product, issue)
    except Exception as e:
        handle_task_exception(e, user)


def issue_tracker_factory(product: Product, with_communication: bool = True) -> BaseIssueTracker:
    if product.issue_tracker_type == Issue_Tracker.ISSUE_TRACKER_GITHUB:
        return GitHubIssueTracker()

    if product.issue_tracker_type == Issue_Tracker.ISSUE_TRACKER_GITLAB:
        return GitLabIssueTracker()

    if product.issue_tracker_type == Issue_Tracker.ISSUE_TRACKER_JIRA:
        return JiraIssueTracker(product=product, with_communication=with_communication)

    raise ValueError(f"Unknown issue tracker type: {product.issue_tracker_type}")


def _get_issue(observation: Observation, issue_tracker: BaseIssueTracker) -> Optional[Issue]:
    if observation.issue_tracker_issue_id:
        issue = issue_tracker.get_issue(observation.product, observation.issue_tracker_issue_id)
    else:
        issue = None
    return issue
