import hashlib
import logging
import secrets
from typing import Any

import requests
from django.db import DatabaseError, IntegrityError
from django.utils.text import slugify
from huey.contrib.djhuey import on_commit_task
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from application.commons.models import Settings
from application.commons.services.log_message import format_log_message
from application.core.models import Product
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.queries.scancodeio_project import (
    get_scancodeio_project_by_product,
)
from application.scancodeio.types import CreateProjectParameters

logger = logging.getLogger("secobserve.scancodeio")

SCANCODEIO_REQUEST_TIMEOUT = 5 * 60

# Like the ScanCode.io UI (get_pipeline_choices(include_addon=False)), projects are created with
# one pipeline that is not an add-on. The REST API doesn't tell which pipelines are add-ons,
# so the list is taken from ScanCode.io v38.2.0.
SCANCODEIO_ADDON_PIPELINES = frozenset(
    {
        "analyze_symbols_reachability",
        "benchmark_purls",
        "collect_strings_gettext",
        "collect_symbols_ctags",
        "collect_symbols_pygments",
        "collect_symbols_tree_sitter",
        "enrich_with_purldb",
        "fetch_scores",
        "find_origins",
        "find_vulnerabilities",
        "fingerprint_codebase",
        "inspect_elf_binaries",
        "match_to_matchcode",
        "populate_purldb",
        "publish_to_federatedcode",
        "scan_for_virus",
    }
)

# Hack for the development environment: http://nginx is only reachable between the containers,
# the browser reaches ScanCode.io with the published port
SCANCODEIO_DEV_BASE_URL = "http://nginx"
SCANCODEIO_DEV_UI_URL = "http://localhost:4100"


class ScanCodeIOClient:
    def __init__(self) -> None:
        settings = Settings.load()
        self.base_url = settings.scancodeio_base_url.rstrip("/")
        self.api_key = settings.scancodeio_api_key
        self.headers = {"Accept": "application/json", "Authorization": f"Token {self.api_key}"}

    def get_pipelines(self) -> list[dict[str, str]]:
        response = self._request("get", "/api/projects/pipelines/")
        return [
            {"name": pipeline.get("name"), "summary": pipeline.get("summary", "")}
            for pipeline in response
            if pipeline.get("is_available", True) and pipeline.get("name") not in SCANCODEIO_ADDON_PIPELINES
        ]

    def create_project(self, parameters: CreateProjectParameters, webhook_url: str) -> dict[str, Any]:
        data = {
            "name": parameters.name,
            "input_urls": parameters.input_urls,
            "pipeline": parameters.pipeline,
            "execute_now": "true" if parameters.execute_now else "false",
            "webhook_url": webhook_url,
        }
        files = None
        if parameters.upload_file:
            files = {"upload_file": (parameters.upload_file.name, parameters.upload_file)}

        return self._request("post", "/api/projects/", data=data, files=files)

    def get_project(self, project_uuid: str) -> dict[str, Any]:
        return self._request("get", f"/api/projects/{project_uuid}/")

    def delete_project(self, project_uuid: str) -> None:
        # A project that has already been deleted in ScanCode.io is no reason to keep it in SecObserve
        self._request("delete", f"/api/projects/{project_uuid}/", ignore_not_found=True)

    def _request(self, method: str, path: str, ignore_not_found: bool = False, **kwargs: Any) -> Any:
        if not self.base_url:
            raise ValidationError("ScanCode.io base URL is not set")
        if not self.api_key:
            raise ValidationError("ScanCode.io API key is not set")

        try:
            response = requests.request(
                method,
                self.base_url + path,
                headers=self.headers,
                timeout=SCANCODEIO_REQUEST_TIMEOUT,
                **kwargs,
            )
        except requests.exceptions.RequestException as e:
            logger.warning(format_log_message(message="ScanCode.io request failed", exception=e))
            raise ValidationError(f"ScanCode.io is not reachable: {e}") from e

        if ignore_not_found and response.status_code == HTTP_404_NOT_FOUND:
            return None

        if not response.ok:
            raise ValidationError(f"ScanCode.io error: {self._error_message(response)}")

        if response.status_code == HTTP_204_NO_CONTENT:
            return None

        return response.json()

    def _error_message(self, response: requests.Response) -> str:
        try:
            errors = response.json()
        except ValueError:
            return f"{response.status_code} {response.reason}"

        if isinstance(errors, dict):
            messages = []
            for field, field_errors in errors.items():
                if isinstance(field_errors, list):
                    field_errors = ", ".join(str(error) for error in field_errors)
                messages.append(f"{field}: {field_errors}")
            return "; ".join(messages)

        return str(errors)


def get_scancodeio_pipelines() -> list[dict[str, str]]:
    return ScanCodeIOClient().get_pipelines()


def get_scancodeio_project_details(scancodeio_project: ScanCodeIO_Project) -> dict[str, Any]:
    details = ScanCodeIOClient().get_project(str(scancodeio_project.project_uuid))
    details["ui_url"] = get_scancodeio_project_ui_url(scancodeio_project)
    return details


def get_scancodeio_project_ui_url(scancodeio_project: ScanCodeIO_Project) -> str:
    base_url = Settings.load().scancodeio_base_url.rstrip("/")
    if base_url == SCANCODEIO_DEV_BASE_URL:
        base_url = SCANCODEIO_DEV_UI_URL

    # Same slug as ScanCode.io builds in get_project_slug()
    slug = f"{slugify(scancodeio_project.project_name)}-{str(scancodeio_project.project_uuid)[0:8]}"
    return f"{base_url}/project/{slug}/"


def delete_scancodeio_project(scancodeio_project: ScanCodeIO_Project) -> None:
    ScanCodeIOClient().delete_project(str(scancodeio_project.project_uuid))
    scancodeio_project.delete()


def create_scancodeio_project(product: Product, parameters: CreateProjectParameters) -> ScanCodeIO_Project:
    if get_scancodeio_project_by_product(product):
        raise ValidationError(f"Product {product.name} already has a ScanCode.io project")

    if not parameters.input_urls and not parameters.upload_file:
        raise ValidationError("At least one input URL or a file to upload is required")

    if parameters.pipeline in SCANCODEIO_ADDON_PIPELINES:
        raise ValidationError(f"Pipeline {parameters.pipeline} is an add-on and cannot be used to create a project")

    webhook_base_url = Settings.load().scancodeio_webhook_base_url.rstrip("/")
    if not webhook_base_url:
        raise ValidationError("SecObserve URL for ScanCode.io webhooks is not set")

    # ScanCode.io sends webhooks without authentication, so the URL contains a secret token
    webhook_token = secrets.token_urlsafe(32)
    webhook_url = f"{webhook_base_url}/api/scancodeio/webhook/{webhook_token}/"
    webhook_token_hash = hash_webhook_token(webhook_token)

    client = ScanCodeIOClient()
    response = client.create_project(parameters, webhook_url)

    try:
        scancodeio_project = ScanCodeIO_Project.objects.create(
            product=product,
            project_uuid=response["uuid"],
            project_name=response["name"],
            webhook_token_hash=webhook_token_hash,
        )
    except DatabaseError as e:
        # Without a reference in SecObserve, the project in ScanCode.io could neither be shown nor deleted
        _delete_orphaned_project(client, response["uuid"])
        if isinstance(e, IntegrityError):
            # A concurrent request has created a project for the product in the meantime
            raise ValidationError(f"Product {product.name} already has a ScanCode.io project") from e
        raise

    return scancodeio_project


@on_commit_task()
def delete_orphaned_scancodeio_project(project_uuid: str) -> None:
    _delete_orphaned_project(ScanCodeIOClient(), project_uuid)


def _delete_orphaned_project(client: ScanCodeIOClient, project_uuid: str) -> None:
    # There is no reference in SecObserve anymore, so a failure can only be logged
    try:
        client.delete_project(project_uuid)
    except ValidationError as e:
        logger.warning(
            format_log_message(message=f"Orphaned ScanCode.io project {project_uuid} could not be deleted", exception=e)
        )


def hash_webhook_token(webhook_token: str) -> str:
    # The token is random with 256 bits, so a fast hash is sufficient and allows to look it up
    return hashlib.sha256(webhook_token.encode("utf-8")).hexdigest()


def process_scancodeio_webhook(scancodeio_project: ScanCodeIO_Project, payload: dict[str, Any]) -> None:
    # Dummy implementation, the results will be imported into SecObserve later
    run = payload.get("run", {})
    logger.info(
        format_log_message(
            message=f"ScanCode.io webhook for project {scancodeio_project.project_name}: "
            + f"pipeline {run.get('pipeline_name')} finished with status {run.get('status')}"
        )
    )
