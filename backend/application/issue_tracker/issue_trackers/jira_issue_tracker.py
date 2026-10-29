from typing import Optional

from jira.client import JIRA
from jira.exceptions import JIRAError
from jira.resources import Issue as JiraIssue

from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation, Product
from application.issue_tracker.issue_trackers.base_issue_tracker import (
    BaseIssueTracker,
    Issue,
)


class JiraIssueTracker(BaseIssueTracker):
    def __init__(self, product: Product, with_communication: bool = True) -> None:
        if with_communication:
            self.jira = JIRA(
                server=product.issue_tracker_base_url,
                basic_auth=(
                    product.issue_tracker_username,
                    product.issue_tracker_api_key,
                ),
            )
            # The JIRA client has no option to disable redirects, the request for the server info
            # in the constructor still follows them.
            self.jira._session.max_redirects = 0  # pylint: disable=protected-access

    def create_issue(self, observation: Observation) -> str:
        labels = observation.product.issue_tracker_labels.split(",")

        jira_issue = self.jira.create_issue(
            project=observation.product.issue_tracker_project_id,
            summary=self._get_title(observation),
            description=self._get_description(observation),
            labels=[item.strip() for item in labels],
            issuetype=observation.product.issue_tracker_issue_type,
        )

        observation.issue_tracker_jira_initial_status = str(jira_issue.fields.status)
        observation.save()

        return jira_issue.key

    def get_issue(self, product: Product, issue_id: str) -> Optional[Issue]:
        jira_issue = self._get_jira_issue(issue_id)
        if not jira_issue:
            return None

        return Issue(
            id=issue_id,
            title=jira_issue.fields.summary,
            description=jira_issue.fields.description,
            labels=",".join(jira_issue.fields.labels),
        )

    def update_issue(self, observation: Observation, issue: Issue) -> None:
        if not observation.issue_tracker_issue_id:
            return

        jira_issue = self._get_jira_issue(issue.id)

        if jira_issue:
            jira_issue.update(
                summary=self._get_title(observation),
                description=self._get_description(observation),
            )

            if (
                jira_issue.fields.status
                and str(jira_issue.fields.status) == observation.product.issue_tracker_status_closed
                and observation.issue_tracker_jira_initial_status
            ):
                self.jira.transition_issue(jira_issue, observation.issue_tracker_jira_initial_status)

    def close_issue(self, observation: Observation, issue: Issue) -> None:
        if not observation.issue_tracker_issue_id:
            return

        description = self._get_description(observation)
        description += f"\n\n*Observation status:* {observation.current_status}"

        jira_issue = self._get_jira_issue(issue.id)

        if jira_issue:
            jira_issue.update(
                summary=self._get_title(observation),
                description=description,
            )

            self.jira.transition_issue(jira_issue, observation.product.issue_tracker_status_closed)

    def close_issue_for_deleted_observation(self, product: Product, issue: Issue) -> None:
        jira_issue = self._get_jira_issue(issue.id)

        if jira_issue:
            description = self._get_description_for_deleted_observation(jira_issue.fields.description)
            description = description.replace("**", "*")

            jira_issue.update(
                summary=jira_issue.fields.summary,
                description=description,
            )

            self.jira.transition_issue(jira_issue, product.issue_tracker_status_closed)

    def get_frontend_issue_url(self, product: Product, issue_id: str) -> str:
        return f"{product.issue_tracker_base_url}/browse/{issue_id}"

    def _get_description(self, observation: Observation) -> str:
        description = observation.description
        description = description.replace("**", "*")
        description = description.replace("```", "{code}")

        if observation.branch:
            description += f"\n\n*Branch:* {observation.branch.name}"

        url = f"{get_base_url_frontend()}#/observations/{observation.pk}/show"
        description += f"\n\n*SecObserve observation:* {url}"

        return description

    def _get_jira_issue(self, issue_id: str) -> Optional[JiraIssue]:
        try:
            return self.jira.issue(issue_id, fields="summary,description,labels,status")
        except JIRAError as e:
            if e.status_code == 404:
                return None
            raise
