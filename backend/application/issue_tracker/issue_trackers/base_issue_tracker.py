from dataclasses import dataclass
from typing import Optional

from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation, Product


@dataclass
class Issue:
    id: str
    title: str
    description: Optional[str] = None
    labels: Optional[str] = None


class BaseIssueTracker:
    def create_issue(self, observation: Observation) -> str:
        raise NotImplementedError("create_issue() must be overridden")

    def get_issue(self, product: Product, issue_id: str) -> Optional[Issue]:
        raise NotImplementedError("get_issue() must be overridden")

    def update_issue(self, observation: Observation, issue: Issue) -> None:
        raise NotImplementedError("update_issue() must be overridden")

    def close_issue(self, observation: Observation, issue: Issue) -> None:
        raise NotImplementedError("close_issue() must be overridden")

    def close_issue_for_deleted_observation(self, product: Product, issue: Issue) -> None:
        raise NotImplementedError("close_issue() must be overridden")

    def get_frontend_issue_url(self, product: Product, issue_id: str) -> str:
        raise NotImplementedError("get_frontend_issue_url() must be overridden")

    def _get_title(self, observation: Observation) -> str:
        title = f'{observation.current_severity} vulnerability: "{observation.title}"'
        origin = self._get_origin(observation)
        if origin:
            title += f" in {origin}"
        return title

    def _get_description(self, observation: Observation) -> str:
        description = observation.description

        if observation.branch:
            description += f"\n\n**Branch:** {observation.branch.name}"

        url = f"{get_base_url_frontend()}#/observations/{observation.pk}/show"
        description += f"\n\n**SecObserve observation:** [{url}]({url})"

        return description

    def _get_origin(self, observation: Observation) -> str:
        origin = ""
        if observation.origin_service:
            origin += f"{observation.origin_service.name}"
        if observation.origin_component_name_version:
            if origin:
                origin += " / "
            origin += f"{observation.origin_component_name_version}"
        if observation.origin_docker_image_name_tag_short:
            if origin:
                origin += " / "
            origin += f"{observation.origin_docker_image_name_tag_short}"
        if observation.origin_endpoint_hostname:
            if origin:
                origin += " / "
            origin += f"{observation.origin_endpoint_hostname}"
        if observation.origin_source_file:
            if origin:
                origin += " / "
            origin += f"{observation.origin_source_file}"
        if observation.origin_cloud_provider:
            if origin:
                origin += " / "
            origin += f"{observation.origin_cloud_provider} / "
            origin += f"{observation.origin_cloud_account_subscription_project} / "
            origin += f"{observation.origin_cloud_resource}"
        return origin

    def _get_description_for_deleted_observation(self, description: Optional[str]) -> str:
        return f"**--- Observation has been deleted ---**\n\n{description}"

    def _normalize_base_url(self, base_url: str) -> str:
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        return base_url
