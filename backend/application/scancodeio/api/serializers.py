import ipaddress
import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator, URLValidator
from packageurl import PackageURL
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    CharField,
    DateTimeField,
    FileField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    UUIDField,
)

from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.types import SCANCODEIO_PROJECT_NAME_MAX_LENGTH

# Same pattern as ScanCode.io uses to validate Docker references
DOCKER_REFERENCE_PATTERN = re.compile(r"^docker://[a-zA-Z0-9_.:/@-]+$")

HTTP_URL_MESSAGE = (
    "Enter an http(s) URL, a Docker reference (docker://), a Git repository (.git) or a package URL (pkg:)."
)
INTERNAL_ADDRESS_MESSAGE = "Loopback, link-local and other non-routable addresses are not allowed."


def validate_input_url(value: str) -> None:
    # The checks follow the input types ScanCode.io can fetch, see get_fetcher() in scanpipe/pipes/fetch.py
    if value.startswith("git@"):
        raise ValidationError("SSH URLs are not supported, use https:// instead.")

    if value.startswith("docker://"):
        if not DOCKER_REFERENCE_PATTERN.match(value):
            raise ValidationError("Invalid Docker reference.")
        # ScanCode.io only checks http(s) URLs for internal addresses, not Docker references
        if _is_internal_host(_get_docker_registry_host(value)):
            raise ValidationError(INTERNAL_ADDRESS_MESSAGE)
        return

    if value.startswith("pkg:"):
        _validate_package_url(value)
        return

    _validate_http_url(value)


def _validate_package_url(value: str) -> None:
    # ScanCode.io splits every input URL at whitespace, so that the parts behind it would be fetched without having
    # been checked here. These could be file:// or git:// URLs, which don't have to be valid for a package URL.
    if len(value.split()) > 1:
        raise ValidationError("Invalid package URL.")

    try:
        package_url = PackageURL.from_string(value)
    except ValueError as e:
        raise ValidationError("Invalid package URL.") from e

    # ScanCode.io downloads the package from this URL, if it cannot derive a URL from the package URL itself
    qualifiers = package_url.qualifiers if isinstance(package_url.qualifiers, dict) else {}
    download_url = qualifiers.get("download_url")
    if download_url:
        _validate_http_url(download_url)


def _validate_http_url(value: str) -> None:
    try:
        URLValidator(schemes=["http", "https"])(value)
    except DjangoValidationError as e:
        raise ValidationError(HTTP_URL_MESSAGE) from e

    # ScanCode.io checks URLs for internal addresses only if they start with a lower case http
    if not value.startswith("http"):
        raise ValidationError(HTTP_URL_MESSAGE)

    split_url = urlsplit(value)
    # Credentials would be shown to all users who can see the product
    if "@" in split_url.netloc:
        raise ValidationError("URLs with credentials are not supported.")

    if _is_internal_host(split_url.hostname or ""):
        raise ValidationError(INTERNAL_ADDRESS_MESSAGE)


def _get_docker_registry_host(docker_reference: str) -> str:
    registry = docker_reference.removeprefix("docker://").split("/", 1)[0]
    return registry.rpartition("@")[2].partition(":")[0]


def _is_internal_host(host: str) -> bool:
    # Private addresses are allowed on purpose, because internal Git servers and registries are legitimate sources.
    # Host names are not resolved, because ScanCode.io could get a different result than SecObserve. So this
    # doesn't replace restricting the network access of ScanCode.io.
    host = host.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return True

    try:
        ip_addr = ipaddress.ip_address(host)
    except ValueError:
        return False

    ip_addr = getattr(ip_addr, "ipv4_mapped", None) or ip_addr
    return (
        ip_addr.is_loopback
        or ip_addr.is_link_local
        or ip_addr.is_multicast
        or ip_addr.is_reserved
        or ip_addr.is_unspecified
    )


class CreateScanCodeIOProjectSerializer(Serializer):
    name = CharField(max_length=SCANCODEIO_PROJECT_NAME_MAX_LENGTH, required=False, allow_blank=True, default="")
    branch = IntegerField(validators=[MinValueValidator(0)], required=False)
    service = IntegerField(validators=[MinValueValidator(0)], required=False)
    input_urls = ListField(
        child=CharField(max_length=2048, validators=[validate_input_url]), required=False, default=list
    )
    upload_file = FileField(max_length=255, required=False)
    pipeline = CharField(max_length=255)
    execute_now = BooleanField(required=False, default=False)


class ScanCodeIOProjectSerializer(ModelSerializer):
    branch_name = SerializerMethodField()
    service_name = SerializerMethodField()

    class Meta:
        model = ScanCodeIO_Project
        fields = [
            "id",
            "product",
            "branch",
            "branch_name",
            "service",
            "service_name",
            "project_uuid",
            "project_name",
            "created",
        ]

    def get_branch_name(self, obj: ScanCodeIO_Project) -> str:
        return obj.branch.name if obj.branch else ""

    def get_service_name(self, obj: ScanCodeIO_Project) -> str:
        return obj.service.name if obj.service else ""


class ScanCodeIOImportResultsResponseSerializer(Serializer):
    license_components_new = IntegerField()
    license_components_updated = IntegerField()
    license_components_deleted = IntegerField()


class ScanCodeIOPipelineSerializer(Serializer):
    name = CharField()
    summary = CharField()


class ScanCodeIOInputSourceSerializer(Serializer):
    filename = CharField()
    download_url = CharField()
    is_uploaded = BooleanField()


class ScanCodeIORunSerializer(Serializer):
    pipeline_name = CharField()
    status = CharField()
    task_start_date = DateTimeField(allow_null=True)
    task_end_date = DateTimeField(allow_null=True)
    execution_time = IntegerField(allow_null=True)


class ScanCodeIOProjectDetailsSerializer(Serializer):
    name = CharField()
    uuid = UUIDField()
    created_date = DateTimeField()
    input_sources = ScanCodeIOInputSourceSerializer(many=True)
    runs = ScanCodeIORunSerializer(many=True)
    message_count = IntegerField()
    resource_count = IntegerField()
    package_count = IntegerField()
    dependency_count = IntegerField()
    relation_count = IntegerField()
    ui_url = CharField()
