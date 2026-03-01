from typing import Any, Optional

from application.core.models import Branch, Observation, Product
from application.import_observations.parsers.base_parser import (
    BaseFileParser,
    BaseParser,
)
from application.import_observations.types import Parser_Filetype, Parser_Type


class SecObserveParser(BaseParser, BaseFileParser):
    @classmethod
    def get_name(cls) -> str:
        return "SecObserve"

    @classmethod
    def get_filetype(cls) -> str:
        return Parser_Filetype.FILETYPE_JSON

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_OTHER

    def check_format(self, data: Any) -> bool:
        if isinstance(data, dict) and data.get("format") == "SecObserve":
            return True
        return False

    def get_observations(self, data: dict, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        observations: list[Observation] = []

        for uploaded_observation in data.get("observations", []):
            observation = Observation(
                title=uploaded_observation.get("title"),
                description=uploaded_observation.get("description"),
                recommendation=uploaded_observation.get("recommendation"),
                parser_severity=uploaded_observation.get("parser_severity"),
                scanner_observation_id=uploaded_observation.get("scanner_observation_id"),
                vulnerability_id=uploaded_observation.get("vulnerability_id"),
                origin_component_name=uploaded_observation.get("origin_component_name"),
                origin_component_version=uploaded_observation.get("origin_component_version"),
                origin_component_name_version=uploaded_observation.get("origin_component_name_version"),
                origin_component_purl=uploaded_observation.get("origin_component_purl"),
                origin_component_cpe=uploaded_observation.get("origin_component_cpe"),
                origin_docker_image_name=uploaded_observation.get("origin_docker_image_name"),
                origin_docker_image_tag=uploaded_observation.get("origin_docker_image_tag"),
                origin_docker_image_name_tag=uploaded_observation.get("origin_docker_image_name_tag"),
                origin_endpoint_url=uploaded_observation.get("origin_endpoint_url"),
                origin_source_file=uploaded_observation.get("origin_source_file"),
                origin_source_line_start=uploaded_observation.get("origin_source_line_start"),
                origin_source_line_end=uploaded_observation.get("origin_source_line_end"),
                cvss3_score=uploaded_observation.get("cvss3_score"),
                cvss3_vector=uploaded_observation.get("cvss3_vector"),
                cwe=uploaded_observation.get("cwe"),
                scanner=uploaded_observation.get("scanner"),
            )
            reference = uploaded_observation.get("reference")
            if reference:
                observation.unsaved_references = [reference]
            observations.append(observation)

        scanner = observations[0].scanner if observations else self.get_name()
        return observations, scanner
