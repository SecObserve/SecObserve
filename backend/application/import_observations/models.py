from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    PROTECT,
    RESTRICT,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    Index,
    IntegerField,
    Model,
    TextField,
)
from encrypted_model_fields.fields import EncryptedCharField

from application.core.models import Branch, Product, Service
from application.import_observations.types import Parser_Source, Parser_Type


class Parser(Model):
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=16, choices=Parser_Type.TYPE_CHOICES)
    source = CharField(max_length=16, choices=Parser_Source.SOURCE_CHOICES)
    sbom = BooleanField(default=False)
    module_name = CharField(max_length=255, blank=True)
    class_name = CharField(max_length=255, blank=True)

    class Meta:
        db_table = "core_parser"
        indexes = [
            Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Api_Configuration(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    name = CharField(max_length=255)
    parser = ForeignKey(Parser, on_delete=PROTECT)
    base_url = CharField(max_length=255)
    project_key = CharField(max_length=255, blank=True)
    api_key = EncryptedCharField(max_length=255, blank=True)  # nosemgrep
    # We treat EncryptedCharField as a regular CharField
    query = CharField(max_length=255, blank=True)
    basic_auth_enabled = BooleanField(default=False)
    basic_auth_username = CharField(max_length=255, blank=True)
    basic_auth_password = EncryptedCharField(max_length=255, blank=True)  # nosemgrep
    # We treat EncryptedCharField as a regular CharField
    verify_ssl = BooleanField(default=False)
    automatic_import_enabled = BooleanField(default=False)
    automatic_import_branch = ForeignKey(Branch, on_delete=RESTRICT, null=True)
    automatic_import_service = ForeignKey(Service, on_delete=RESTRICT, null=True)
    automatic_import_service_legacy = CharField(max_length=255, blank=True)
    automatic_import_docker_image_name_tag = CharField(max_length=513, blank=True)
    automatic_import_endpoint_url = CharField(max_length=2048, blank=True)
    automatic_import_kubernetes_cluster = CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (
            "product",
            "name",
        )

    def __str__(self) -> str:
        return f"{self.product.name} / {self.name}"


class Vulnerability_Check(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    branch = ForeignKey(Branch, on_delete=CASCADE, null=True)
    service = ForeignKey(Service, on_delete=CASCADE, null=True)
    filename = CharField(max_length=255, blank=True)
    api_configuration_name = CharField(max_length=255, blank=True)
    scanner = CharField(max_length=255, blank=True)
    first_import = DateTimeField(auto_now_add=True)
    last_import = DateTimeField(auto_now=True)
    last_import_observations_new = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    last_import_observations_updated = IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)]
    )
    last_import_observations_resolved = IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)]
    )
    last_import_licenses_new = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    last_import_licenses_updated = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    last_import_licenses_deleted = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])

    class Meta:
        unique_together = (
            "product",
            "branch",
            "service",
            "filename",
            "api_configuration_name",
        )


class OSV_Cache(Model):
    osv_id = CharField(max_length=255, unique=True)
    data = TextField()
    modified = DateTimeField()

    def __str__(self) -> str:
        return self.osv_id
