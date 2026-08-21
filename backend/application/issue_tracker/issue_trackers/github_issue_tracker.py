import json
from typing import Any, Optional

import requests

from application.core.models import Observation, Product
from application.issue_tracker.issue_trackers.base_issue_tracker import (
    BaseIssueTracker,
    Issue,
)


class GitHubIssueTracker(BaseIssueTracker):
    def create_issue(self, observation: Observation) -> str:
        data: dict[str, Any] = {
            "title": self._get_title(observation),
            "body": self._get_description(observation),
        }
        if observation.product.issue_tracker_labels:
            labels = observation.product.issue_tracker_labels.split(",")
            data["labels"] = [item.strip() for item in labels]

        response = requests.post(
            url=self._get_issue_tracker_base_url(observation.product),
            headers=self._get_headers(observation.product),
            data=json.dumps(data),
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("number")

    def get_issue(self, product: Product, issue_id: str) -> Optional[Issue]:
        response = requests.get(
            url=f"{self._get_issue_tracker_base_url(product)}/{issue_id}",
            headers=self._get_headers(product),
            timeout=60,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()

        issue = Issue(
            id=response.json().get("number"),
            title=response.json().get("title"),
            description=response.json().get("body"),
        )

        if response.json().get("labels"):
            issue.labels = ""
            for label in response.json().get("labels"):
                issue.labels += f"{label.get('name')},"
            issue.labels = issue.labels[:-1]

        return issue

    def update_issue(self, observation: Observation, issue: Issue) -> None:
        if not observation.issue_tracker_issue_id:
            return

        data: dict[str, Any] = {
            "title": self._get_title(observation),
            "body": self._get_description(observation),
            "state": "open",
        }
        if observation.product.issue_tracker_labels:
            data["labels"] = self._get_labels(observation.product, issue)

        response = requests.patch(
            url=f"{self._get_issue_tracker_base_url(observation.product)}/{observation.issue_tracker_issue_id}",
            headers=self._get_headers(observation.product),
            data=json.dumps(data),
            timeout=60,
        )
        response.raise_for_status()

    def close_issue(self, observation: Observation, issue: Issue) -> None:
        if not observation.issue_tracker_issue_id:
            return

        description = self._get_description(observation)
        description += f"\n\n**Observation status:** {observation.current_status}"

        data: dict[str, Any] = {
            "title": self._get_title(observation),
            "body": description,
            "state": "closed",
        }
        if observation.product.issue_tracker_labels:
            data["labels"] = self._get_labels(observation.product, issue)

        response = requests.patch(
            url=f"{self._get_issue_tracker_base_url(observation.product)}/{observation.issue_tracker_issue_id}",
            headers=self._get_headers(observation.product),
            data=json.dumps(data),
            timeout=60,
        )
        response.raise_for_status()

    def close_issue_for_deleted_observation(self, product: Product, issue: Issue) -> None:
        data: dict[str, Any] = {
            "body": self._get_description_for_deleted_observation(issue.description),
            "state": "closed",
        }
        if product.issue_tracker_labels:
            data["labels"] = self._get_labels(product, issue)

        response = requests.patch(
            url=f"{self._get_issue_tracker_base_url(product)}/{issue.id}",
            headers=self._get_headers(product),
            data=json.dumps(data),
            timeout=60,
        )
        response.raise_for_status()

    def get_frontend_issue_url(self, product: Product, issue_id: str) -> str:
        base_url = self._normalize_base_url(product.issue_tracker_base_url or "https://api.github.com")
        if base_url.endswith("/api/v3"):
            # GitHub Enterprise Server: API at https://github.example.com/api/v3
            host = base_url[: -len("/api/v3")]
        else:
            host = "https://github.com"
        return f"{host}/{product.issue_tracker_project_id}/issues/{issue_id}"

    def _get_issue_tracker_base_url(self, product: Product) -> str:
        base_url = self._normalize_base_url(product.issue_tracker_base_url or "https://api.github.com")
        return f"{base_url}/repos/{product.issue_tracker_project_id}/issues"

    def _get_headers(self, product: Product) -> dict:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {product.issue_tracker_api_key}",
        }

    def _get_labels(self, product: Product, issue: Issue) -> list[str]:
        product_labels = product.issue_tracker_labels.split(",")
        product_labels = [item.strip() for item in product_labels]

        if issue.labels:
            for label in issue.labels.split(","):
                if label not in product_labels:
                    product_labels.append(label)

        return product_labels
