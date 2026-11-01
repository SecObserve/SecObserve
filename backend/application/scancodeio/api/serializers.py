import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
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
    UUIDField,
)

from application.scancodeio.models import ScanCodeIO_Project

# Same pattern as ScanCode.io uses to validate Docker references
DOCKER_REFERENCE_PATTERN = re.compile(r"^docker://[a-zA-Z0-9_.:/@-]+$")


def validate_input_url(value: str) -> None:
    # The checks follow the input types ScanCode.io can fetch, see get_fetcher() in scanpipe/pipes/fetch.py
    if value.startswith("git@"):
        raise ValidationError("SSH URLs are not supported, use https:// instead.")

    if value.startswith("docker://"):
        if not DOCKER_REFERENCE_PATTERN.match(value):
            raise ValidationError("Invalid Docker reference.")
        return

    if value.startswith("pkg:"):
        try:
            PackageURL.from_string(value)
        except ValueError as e:
            raise ValidationError("Invalid package URL.") from e
        return

    try:
        URLValidator(schemes=["http", "https"])(value)
    except DjangoValidationError as e:
        raise ValidationError(
            "Enter an http(s) URL, a Docker reference (docker://), a Git repository (.git) or a package URL (pkg:)."
        ) from e


class CreateScanCodeIOProjectSerializer(Serializer):
    name = CharField(max_length=255)
    input_urls = ListField(
        child=CharField(max_length=2048, validators=[validate_input_url]), required=False, default=list
    )
    upload_file = FileField(max_length=255, required=False)
    pipeline = CharField(max_length=255)
    execute_now = BooleanField(required=False, default=False)


class ScanCodeIOProjectSerializer(ModelSerializer):
    class Meta:
        model = ScanCodeIO_Project
        fields = ["id", "product", "project_uuid", "project_name", "created"]


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
