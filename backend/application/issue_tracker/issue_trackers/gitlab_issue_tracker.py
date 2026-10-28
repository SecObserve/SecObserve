import urllib.parse
from typing import Optional

import requests

from application.core.models import Observation, Product
from application.issue_tracker.issue_trackers.base_issue_tracker import (
    BaseIssueTracker,
    Issue,
)


class GitLabIssueTracker(BaseIssueTracker):
    def create_issue(self, observation: Observation) -> str:
        data = {
            "title": self._get_title(observation),
            "description": self._get_description(observation),
            "confidential": True,
        }
        if observation.product.issue_tracker_labels:
            data["labels"] = observation.product.issue_tracker_labels
        response = requests.post(
            url=self._get_issue_tracker_base_url(observation.product),
            headers=self._get_headers(observation.product),
            data=data,
            timeout=60,
            allow_redirects=False,
        )
        response.raise_for_status()
        return response.json().get("iid")

    def get_issue(self, product: Product, issue_id: str) -> Optional[Issue]:
        response = requests.get(
            url=f"{self._get_issue_tracker_base_url(product)}/{issue_id}",
            headers=self._get_headers(product),
            timeout=60,
            allow_redirects=False,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()

        issue = Issue(
            id=response.json().get("iid"),
            title=response.json().get("title"),
            description=response.json().get("description"),
            labels=",".join(response.json().get("labels")),
        )

        return issue

    def update_issue(self, observation: Observation, issue: Issue) -> None:
        if not observation.issue_tracker_issue_id:
            return

        data = {
            "title": self._get_title(observation),
            "description": self._get_description(observation),
            "confidential": True,
            "state_event": "reopen",
        }
        if observation.product.issue_tracker_labels:
            data["add_labels"] = observation.product.issue_tracker_labels
        response = requests.put(
            url=f"{self._get_issue_tracker_base_url(observation.product)}/{observation.issue_tracker_issue_id}",
            headers=self._get_headers(observation.product),
            data=data,
            timeout=60,
            allow_redirects=False,
        )
        response.raise_for_status()

    def close_issue(self, observation: Observation, issue: Issue) -> None:
        if not observation.issue_tracker_issue_id:
            return

        description = self._get_description(observation)
        description += f"\n\n**Observation status:** {observation.current_status}"

        data = {
            "title": self._get_title(observation),
            "description": description,
            "confidential": True,
            "state_event": "close",
        }
        if observation.product.issue_tracker_labels:
            data["add_labels"] = observation.product.issue_tracker_labels
        response = requests.put(
            url=f"{self._get_issue_tracker_base_url(observation.product)}/{observation.issue_tracker_issue_id}",
            headers=self._get_headers(observation.product),
            data=data,
            timeout=60,
            allow_redirects=False,
        )
        response.raise_for_status()

    def close_issue_for_deleted_observation(self, product: Product, issue: Issue) -> None:
        data = {
            "description": self._get_description_for_deleted_observation(issue.description),
            "confidential": True,
            "state_event": "close",
        }
        if product.issue_tracker_labels:
            data["add_labels"] = product.issue_tracker_labels
        response = requests.put(
            url=f"{self._get_issue_tracker_base_url(product)}/{issue.id}",
            headers=self._get_headers(product),
            data=data,
            timeout=60,
            allow_redirects=False,
        )
        response.raise_for_status()

    def get_frontend_issue_url(self, product: Product, issue_id: str) -> str:
        base_url = self._normalize_base_url(product.issue_tracker_base_url)
        return f"{base_url}/{product.issue_tracker_project_id}/-/issues/{issue_id}"

    def _get_issue_tracker_base_url(self, product: Product) -> str:
        base_url = self._normalize_base_url(product.issue_tracker_base_url)
        return f"{base_url}/api/v4/projects/{urllib.parse.quote_plus(product.issue_tracker_project_id)}/issues"

    def _get_headers(self, product: Product) -> dict:
        return {
            "PRIVATE-TOKEN": product.issue_tracker_api_key,
        }
