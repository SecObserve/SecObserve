from typing import Optional
from urllib.parse import urlparse

from django.utils import timezone
from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from application.access_control.services.current_user import get_current_user
from application.commons.services.functions import get_comma_separated_as_list
from application.core.api.serializers_helpers import (
    get_branch_name,
    get_origin_component_name_version,
    get_origin_service_name,
    get_scanner_name,
    validate_cvss3_vector,
    validate_cvss4_vector,
    validate_cvss_and_severity,
    validate_url,
)
from application.core.api.serializers_product import (
    NestedProductListSerializer,
    NestedProductSerializer,
)
from application.core.models import (
    Branch,
    Evidence,
    Observation,
    Observation_Log,
    Potential_Duplicate,
    Product,
    Reference,
    Service,
)
from application.core.queries.observation import get_current_observation_log
from application.core.services.observation_log import create_observation_log
from application.core.services.security_gate import check_security_gate_observation
from application.core.types import (
    Assessment_Status,
    Severity,
    Status,
    VEX_Justification,
)
from application.import_observations.api.serializers import ParserSerializer
from application.import_observations.models import Parser
from application.import_observations.types import Parser_Type
from application.issue_tracker.services.issue_tracker import (
    issue_tracker_factory,
    push_observation_to_issue_tracker,
)


class NestedReferenceSerializer(ModelSerializer):
    class Meta:
        model = Reference
        exclude = ["observation"]


class NestedEvidenceSerializer(ModelSerializer):
    class Meta:
        model = Evidence
        exclude = ["observation", "evidence"]


class EvidenceSerializer(ModelSerializer):
    product = SerializerMethodField()

    class Meta:
        model = Evidence
        fields = "__all__"

    def get_product(self, evidence: Evidence) -> int:
        return evidence.observation.product.pk


class ObservationSerializer(ModelSerializer):
    product_data = NestedProductSerializer(source="product")
    branch_name = SerializerMethodField()
    parser_data = ParserSerializer(source="parser")
    references = NestedReferenceSerializer(many=True)
    evidences = NestedEvidenceSerializer(many=True)
    origin_service_name = SerializerMethodField()
    origin_source_file_url = SerializerMethodField()
    issue_tracker_issue_url = SerializerMethodField()
    assessment_needs_approval = SerializerMethodField()
    vulnerability_id_aliases = SerializerMethodField()
    cve_found_in = SerializerMethodField()

    class Meta:
        model = Observation
        exclude = ["numerical_severity", "issue_tracker_jira_initial_status", "origin_source_file_link"]

    def to_representation(self, instance: Observation) -> dict:
        response = super().to_representation(instance)
        response["evidences"] = sorted(response["evidences"], key=lambda x: x["name"])
        return response

    def get_branch_name(self, observation: Observation) -> str:
        return get_branch_name(observation)

    def get_origin_service_name(self, observation: Observation) -> str:
        return get_origin_service_name(observation)

    def get_origin_source_file_url(self, observation: Observation) -> Optional[str]:
        return _get_origin_source_file_url(observation)

    def get_issue_tracker_issue_url(self, observation: Observation) -> Optional[str]:
        issue_url = None

        if observation.issue_tracker_issue_id:
            issue_tracker = issue_tracker_factory(observation.product, with_communication=False)
            issue_url = issue_tracker.get_frontend_issue_url(observation.product, observation.issue_tracker_issue_id)

        return issue_url

    def get_assessment_needs_approval(self, observation: Observation) -> Optional[int]:
        current_observation_log = get_current_observation_log(observation)
        if (
            current_observation_log
            and current_observation_log.assessment_status == Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        ):
            return current_observation_log.pk
        return None

    def get_vulnerability_id_aliases(self, observation: Observation) -> list[dict[str, str]]:
        return _get_vulnerability_id_aliases(observation)

    def get_cve_found_in(self, observation: Observation) -> list[dict[str, str]]:
        return _get_cve_found_in_sources(observation)

    def validate_product(self, product: Product) -> Product:
        if product and product.is_product_group:
            raise ValidationError("Product must not be a product group")

        return product


class ObservationTitleSerializer(ModelSerializer):
    class Meta:
        model = Observation
        fields = ["id", "title"]


class ObservationListSerializer(ModelSerializer):
    product_data = NestedProductListSerializer(source="product")
    branch_name = SerializerMethodField()
    parser_data = ParserSerializer(source="parser")
    scanner_name = SerializerMethodField()
    origin_service_name = SerializerMethodField()
    origin_component_name_version = SerializerMethodField()
    origin_source_file_short = SerializerMethodField()
    origin_source_file_url = SerializerMethodField()
    vulnerability_id_aliases = SerializerMethodField()
    cve_found_in = SerializerMethodField()

    class Meta:
        model = Observation
        exclude = [
            "numerical_severity",
            "issue_tracker_jira_initial_status",
            "origin_component_dependencies",
            "origin_source_file_link",
        ]

    def get_branch_name(self, observation: Observation) -> str:
        return get_branch_name(observation)

    def get_scanner_name(self, observation: Observation) -> str:
        return get_scanner_name(observation)

    def get_origin_service_name(self, observation: Observation) -> str:
        return get_origin_service_name(observation)

    def get_origin_component_name_version(self, observation: Observation) -> str:
        return get_origin_component_name_version(observation)

    def get_origin_source_file_short(self, observation: Observation) -> Optional[str]:
        if observation.origin_source_file:
            source_file_parts = observation.origin_source_file.split("/")
            if len(source_file_parts) > 2:
                return f"{source_file_parts[0]}/.../{source_file_parts[-1]}"
        return observation.origin_source_file

    def get_origin_source_file_url(self, observation: Observation) -> Optional[str]:
        return _get_origin_source_file_url(observation)

    def get_vulnerability_id_aliases(self, observation: Observation) -> list[dict[str, str]]:
        return _get_vulnerability_id_aliases(observation)

    def get_cve_found_in(self, observation: Observation) -> list[dict[str, str]]:
        return _get_cve_found_in_sources(observation)


def _get_origin_source_file_url(observation: Observation) -> Optional[str]:
    origin_source_file_url = None

    if observation.origin_source_file_link:
        return observation.origin_source_file_link

    if observation.product.repository_prefix and observation.origin_source_file:
        if not validate_url(observation.product.repository_prefix):
            return None

        parsed_url = urlparse(observation.product.repository_prefix)

        origin_source_file_url = observation.product.repository_prefix
        if origin_source_file_url.endswith("/"):
            origin_source_file_url = origin_source_file_url[:-1]
        if parsed_url.netloc == "dev.azure.com":
            origin_source_file_url = _create_azure_devops_url(observation, origin_source_file_url)
        else:
            origin_source_file_url = _create_common_url(observation, origin_source_file_url)

    return origin_source_file_url


def _create_azure_devops_url(observation: Observation, origin_source_file_url: str) -> str:
    origin_source_file_url += f"?path={observation.origin_source_file}"
    if observation.branch:
        origin_source_file_url += f"&version=GB{observation.branch.name}"
    if observation.origin_source_line_start:
        origin_source_file_url += f"&line={observation.origin_source_line_start}"
        origin_source_file_url += "&lineStartColumn=1&lineEndColumn=1"
        if observation.origin_source_line_end:
            origin_source_file_url += f"&lineEnd={observation.origin_source_line_end+1}"
        else:
            origin_source_file_url += f"&lineEnd={observation.origin_source_line_start+1}"

    return origin_source_file_url


def _create_common_url(observation: Observation, origin_source_file_url: str) -> str:
    if observation.branch:
        origin_source_file_url += f"/{observation.branch.name}"
    origin_source_file_url += f"/{observation.origin_source_file}"
    if observation.origin_source_line_start:
        origin_source_file_url += "#L" + str(observation.origin_source_line_start)
        if (
            observation.origin_source_line_end
            and observation.origin_source_line_start != observation.origin_source_line_end
        ):
            origin_source_file_url += "-L" + str(observation.origin_source_line_end)

    return origin_source_file_url


def _get_vulnerability_id_aliases(observation: Observation) -> list[dict[str, str]]:
    aliases_list = get_comma_separated_as_list(observation.vulnerability_id_aliases)
    return_list = []
    for alias in aliases_list:
        return_list.append({"alias": alias})
    return return_list


def _get_cve_found_in_sources(observation: Observation) -> list[dict[str, str]]:
    sources_list = get_comma_separated_as_list(observation.cve_found_in)
    return_list = []
    for source in sources_list:
        return_list.append({"source": source})
    return return_list


class ObservationUpdateSerializer(ModelSerializer):
    def validate(self, attrs: dict) -> dict:
        self.instance: Observation
        if self.instance and self.instance.parser.type != Parser_Type.TYPE_MANUAL:
            raise ValidationError("Only manual observations can be updated")

        attrs["import_last_seen"] = timezone.now()

        validate_cvss_and_severity(attrs)

        return super().validate(attrs)

    def validate_branch(self, branch: Branch) -> Branch:
        if branch and branch.product != self.instance.product:
            raise ValidationError("Branch does not belong to the same product as the observation")

        return branch

    def validate_origin_service(self, service: Service) -> Service:
        if service and service.product != self.instance.product:
            raise ValidationError("Service does not belong to the same product as the observation")

        return service

    def validate_cvss3_vector(self, cvss3_vector: str) -> str:
        return validate_cvss3_vector(cvss3_vector)

    def validate_cvss4_vector(self, cvss4_vector: str) -> str:
        return validate_cvss4_vector(cvss4_vector)

    def update(self, instance: Observation, validated_data: dict) -> Observation:
        actual_severity = instance.current_severity
        actual_status = instance.current_status
        actual_vex_justification = instance.current_vex_justification
        actual_risk_acceptance_expiry_date = instance.risk_acceptance_expiry_date

        instance.origin_component_name = ""
        instance.origin_component_version = ""

        instance.origin_docker_image_name = ""
        instance.origin_docker_image_tag = ""
        instance.origin_docker_image_digest = ""

        observation: Observation = super().update(instance, validated_data)

        log_severity = observation.current_severity if actual_severity != observation.current_severity else ""
        log_status = observation.current_status if actual_status != observation.current_status else ""
        log_vex_justification = (
            observation.current_vex_justification
            if actual_vex_justification != observation.current_vex_justification
            else ""
        )
        log_risk_acceptance_expiry_date = (
            observation.risk_acceptance_expiry_date
            if actual_risk_acceptance_expiry_date != observation.risk_acceptance_expiry_date
            else None
        )

        if log_severity or log_status or log_vex_justification or log_risk_acceptance_expiry_date:
            create_observation_log(
                observation=observation,
                severity=log_severity,
                status=log_status,
                comment="Observation changed manually",
                vex_justification=log_vex_justification,
                assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
                risk_acceptance_expiry_date=log_risk_acceptance_expiry_date,
            )

        check_security_gate_observation(observation)
        push_observation_to_issue_tracker(observation, get_current_user())
        if observation.branch:
            observation.branch.last_import = timezone.now()
            observation.branch.save()

        return observation

    def to_representation(self, instance: Observation) -> dict:
        serializer = ObservationSerializer(instance)
        return serializer.data

    class Meta:
        model = Observation
        fields = [
            "branch",
            "title",
            "description",
            "recommendation",
            "parser_severity",
            "parser_status",
            "parser_vex_justification",
            "origin_component_name_version",
            "origin_component_name",
            "origin_component_version",
            "origin_docker_image_name_tag",
            "origin_docker_image_name",
            "origin_docker_image_tag",
            "origin_endpoint_url",
            "origin_service",
            "origin_source_file",
            "origin_source_line_start",
            "origin_source_line_end",
            "origin_cloud_provider",
            "origin_cloud_account_subscription_project",
            "origin_cloud_resource",
            "origin_cloud_resource_type",
            "origin_kubernetes_cluster",
            "origin_kubernetes_namespace",
            "origin_kubernetes_resource_type",
            "origin_kubernetes_resource_name",
            "vulnerability_id",
            "cvss3_score",
            "cvss3_vector",
            "cvss4_score",
            "cvss4_vector",
            "cwe",
            "risk_acceptance_expiry_date",
        ]


class ObservationCreateSerializer(ModelSerializer):
    def validate(self, attrs: dict) -> dict:
        attrs["parser"] = Parser.objects.get(type=Parser_Type.TYPE_MANUAL)
        attrs["scanner"] = Parser_Type.TYPE_MANUAL
        attrs["import_last_seen"] = timezone.now()

        if attrs.get("branch") and attrs["branch"].product != attrs["product"]:
            raise ValidationError("Branch does not belong to the same product as the observation")

        if attrs.get("service") and attrs["service"].product != attrs["product"]:
            raise ValidationError("Service does not belong to the same product as the observation")

        validate_cvss_and_severity(attrs)

        return super().validate(attrs)

    def validate_cvss3_vector(self, cvss3_vector: str) -> str:
        return validate_cvss3_vector(cvss3_vector)

    def validate_cvss4_vector(self, cvss4_vector: str) -> str:
        return validate_cvss4_vector(cvss4_vector)

    def create(self, validated_data: dict) -> Observation:
        observation: Observation = super().create(validated_data)

        create_observation_log(
            observation=observation,
            severity=observation.current_severity,
            status=observation.current_status,
            comment="Observation created manually",
            vex_justification=observation.current_vex_justification,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
            risk_acceptance_expiry_date=observation.risk_acceptance_expiry_date,
        )

        check_security_gate_observation(observation)
        push_observation_to_issue_tracker(observation, get_current_user())
        if observation.branch:
            observation.branch.last_import = timezone.now()
            observation.branch.save()

        return observation

    def to_representation(self, instance: Observation) -> dict:
        serializer = ObservationSerializer(instance)
        return serializer.data

    class Meta:
        model = Observation
        fields = [
            "product",
            "branch",
            "title",
            "description",
            "recommendation",
            "parser_severity",
            "parser_status",
            "parser_vex_justification",
            "origin_component_name_version",
            "origin_component_name",
            "origin_component_version",
            "origin_docker_image_name_tag",
            "origin_docker_image_name",
            "origin_docker_image_tag",
            "origin_endpoint_url",
            "origin_service",
            "origin_source_file",
            "origin_source_line_start",
            "origin_source_line_end",
            "origin_cloud_provider",
            "origin_cloud_account_subscription_project",
            "origin_cloud_resource",
            "origin_cloud_resource_type",
            "origin_kubernetes_cluster",
            "origin_kubernetes_namespace",
            "origin_kubernetes_resource_type",
            "origin_kubernetes_resource_name",
            "vulnerability_id",
            "cvss3_score",
            "cvss3_vector",
            "cvss4_score",
            "cvss4_vector",
            "cwe",
            "risk_acceptance_expiry_date",
        ]


class ObservationAssessmentSerializer(Serializer):
    severity = ChoiceField(choices=Severity.SEVERITY_CHOICES, required=False)
    status = ChoiceField(choices=Status.STATUS_CHOICES, required=False)
    vex_justification = ChoiceField(
        choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES,
        required=False,
        allow_blank=True,
    )
    priority = IntegerField(min_value=1, max_value=99, required=False, allow_null=True)
    risk_acceptance_expiry_date = DateField(required=False, allow_null=True)
    comment = CharField(max_length=4096, required=True)


class ObservationRemoveAssessmentSerializer(Serializer):
    comment = CharField(max_length=4096, required=True)


class ObservationBulkDeleteSerializer(Serializer):
    observations = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class ObservationBulkAssessmentSerializer(Serializer):
    severity = ChoiceField(choices=Severity.SEVERITY_CHOICES, required=False)
    status = ChoiceField(choices=Status.STATUS_CHOICES, required=False)
    priority = IntegerField(min_value=1, max_value=99, required=False, allow_null=True)
    comment = CharField(max_length=4096, required=True)
    observations = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)
    vex_justification = ChoiceField(
        choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES,
        required=False,
        allow_blank=True,
    )
    risk_acceptance_expiry_date = DateField(required=False, allow_null=True)


class ObservationBulkMarkDuplicatesSerializer(Serializer):
    observation_id = IntegerField(min_value=1, required=True)
    potential_duplicates = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class NestedObservationSerializer(ModelSerializer):
    scanner_name = SerializerMethodField()
    origin_service_name = SerializerMethodField()
    origin_component_name_version = SerializerMethodField()
    cve_found_in = SerializerMethodField()

    class Meta:
        model = Observation
        exclude = ["numerical_severity", "issue_tracker_jira_initial_status", "origin_source_file_link"]

    def get_scanner_name(self, observation: Observation) -> str:
        return get_scanner_name(observation)

    def get_origin_service_name(self, observation: Observation) -> str:
        return get_origin_service_name(observation)

    def get_origin_component_name_version(self, observation: Observation) -> str:
        return get_origin_component_name_version(observation)

    def get_cve_found_in(self, observation: Observation) -> list[dict[str, str]]:
        return _get_cve_found_in_sources(observation)


class ObservationLogSerializer(ModelSerializer):
    observation_data = ObservationSerializer(source="observation")
    user_full_name = SerializerMethodField()
    approval_user_full_name = SerializerMethodField()

    def get_user_full_name(self, obj: Observation_Log) -> Optional[str]:
        if obj.user:
            return obj.user.full_name

        return None

    def get_approval_user_full_name(self, obj: Observation_Log) -> Optional[str]:
        if obj.approval_user:
            return obj.approval_user.full_name

        return None

    class Meta:
        model = Observation_Log
        fields = "__all__"


class ObservationLogListSerializer(ModelSerializer):
    observation_data = ObservationListSerializer(source="observation")
    user_full_name = SerializerMethodField()
    approval_user_full_name = SerializerMethodField()

    def get_user_full_name(self, obj: Observation_Log) -> Optional[str]:
        if obj.user:
            return obj.user.full_name

        return None

    def get_approval_user_full_name(self, obj: Observation_Log) -> Optional[str]:
        if obj.approval_user:
            return obj.approval_user.full_name

        return None

    class Meta:
        model = Observation_Log
        fields = "__all__"


class ObservationLogApprovalSerializer(Serializer):
    assessment_status = ChoiceField(choices=Assessment_Status.ASSESSMENT_STATUS_CHOICES_APPROVAL, required=False)
    approval_remark = CharField(max_length=255, required=True)


class ObservationLogBulkApprovalSerializer(Serializer):
    assessment_status = ChoiceField(choices=Assessment_Status.ASSESSMENT_STATUS_CHOICES_APPROVAL, required=False)
    approval_remark = CharField(max_length=255, required=True)
    observation_logs = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class ObservationLogBulkDeleteSerializer(Serializer):
    observation_logs = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class PotentialDuplicateSerializer(ModelSerializer):
    potential_duplicate_observation = NestedObservationSerializer()

    class Meta:
        model = Potential_Duplicate
        fields = "__all__"


class CountSerializer(Serializer):
    count = IntegerField()
