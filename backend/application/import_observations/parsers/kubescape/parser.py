import logging
from dataclasses import dataclass
from json import dumps
from typing import Any, Optional

from application.core.models import Branch, Observation, Product
from application.import_observations.parsers.base_parser import (
    BaseFileParser,
    BaseParser,
)
from application.import_observations.types import Parser_Filetype, Parser_Type

logger = logging.getLogger("secobserve.import_observations.kubescape.parser")


@dataclass
class Resource:
    kind: str
    namespace: str
    name: str
    obj: dict


class KubescapeParser(BaseParser, BaseFileParser):
    def __init__(self) -> None:
        self.resources: dict[str, Resource] = {}

    @classmethod
    def get_name(cls) -> str:
        return "Kubescape"

    @classmethod
    def get_filetype(cls) -> str:
        return Parser_Filetype.FILETYPE_JSON

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_INFRASTRUCTURE

    @classmethod
    def sbom(cls) -> bool:
        return False

    def check_format(self, data: Any) -> bool:
        if isinstance(data, dict) and data.get("metadata") and isinstance(data.get("metadata"), dict):
            metadata = data.get("metadata", {})
            if metadata.get("scanMetadata") and isinstance(metadata.get("scanMetadata"), dict):
                scan_metadata = metadata.get("scanMetadata", {})
                if scan_metadata.get("kubescapeVersion") and scan_metadata.get("formatVersion", "") == "v2":
                    return True
        return False

    def get_observations(self, data: dict, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        observations = []

        self.resources = self._get_resources(data)
        cluster_name = (
            data.get("metadata", {}).get("targetMetadata", {}).get("clusterContextMetadata", {}).get("contextName")
        )
        kubescape_version = data.get("metadata", {}).get("scanMetadata", {}).get("kubescapeVersion")

        results = data.get("results", [])
        for result in results:
            resource = self.resources.get(result.get("resourceID"))
            if resource:
                controls = result.get("controls")
                for control in controls:
                    if control.get("status", {}).get("status") == "failed":
                        control_id = control.get("controlID")
                        name = control.get("name")
                        severity = control.get("severity")

                        observation = Observation(
                            title=f"{control_id} / {name}",
                            parser_severity=severity,
                            origin_kubernetes_cluster=cluster_name,
                            origin_kubernetes_namespace=resource.namespace,
                            origin_kubernetes_resource_type=resource.kind,
                            origin_kubernetes_resource_name=resource.name,
                            scanner=f"Kubescape / {kubescape_version}",
                        )

                        observation.unsaved_references = [f"https://kubescape.io/docs/controls/{control_id.lower()}"]

                        evidence = []
                        evidence.append("Control")
                        evidence.append(dumps(control))
                        observation.unsaved_evidences.append(evidence)

                        evidence = []
                        evidence.append("Resource")
                        evidence.append(dumps(resource.obj))
                        observation.unsaved_evidences.append(evidence)

                        observations.append(observation)

            else:
                logger.warning("Resource %s not found", result.get("resourceID"))

        return observations, f"Kubescape / {kubescape_version}"

    def _get_resources(self, data: dict) -> dict[str, Resource]:
        resource_dict: dict[str, Resource] = {}

        resources = data.get("resources", [])
        for resource in resources:
            obj = resource.get("object")
            metadata = obj.get("metadata")

            kind = obj.get("kind")
            namespace = metadata.get("namespace") if metadata else obj.get("namespace")
            name = metadata.get("name") if metadata else obj.get("name")
            resource_dict[resource.get("resourceID")] = Resource(
                kind=kind, namespace=namespace, name=name, obj=resource
            )

        return resource_dict
