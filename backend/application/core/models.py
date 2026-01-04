from decimal import Decimal
from typing import Any

from dirtyfields import DirtyFieldsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    DO_NOTHING,
    PROTECT,
    SET_NULL,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    Index,
    IntegerField,
    ManyToManyField,
    Model,
    TextField,
)
from django.utils import timezone

from application.access_control.models import Authorization_Group, User
from application.core.types import (
    Assessment_Status,
    OSVLinuxDistribution,
    Severity,
    Status,
    VEX_Justification,
)
from application.issue_tracker.types import Issue_Tracker


class Product(Model, DirtyFieldsMixin):  # pylint: disable=too-many-instance-attributes
    name = CharField(max_length=255, unique=True)
    description = TextField(max_length=2048, blank=True)

    is_product_group = BooleanField(default=False)
    product_group = ForeignKey("self", on_delete=PROTECT, related_name="products", null=True, blank=True)
    purl = CharField(max_length=255, blank=True)
    cpe23 = CharField(max_length=255, blank=True)

    repository_prefix = CharField(max_length=255, blank=True)
    repository_default_branch = ForeignKey(
        "Branch",
        on_delete=SET_NULL,
        related_name="repository_default_branch",
        null=True,
    )
    repository_branch_housekeeping_active = BooleanField(null=True)
    repository_branch_housekeeping_keep_inactive_days = IntegerField(
        null=True, validators=[MinValueValidator(1), MaxValueValidator(999999)]
    )
    repository_branch_housekeeping_exempt_branches = CharField(max_length=255, blank=True)

    security_gate_passed = BooleanField(null=True)
    security_gate_active = BooleanField(null=True)
    security_gate_threshold_critical = IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)]
    )
    security_gate_threshold_high = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    security_gate_threshold_medium = IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)]
    )
    security_gate_threshold_low = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    security_gate_threshold_none = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    security_gate_threshold_unknown = IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)]
    )

    members: ManyToManyField = ManyToManyField(
        User, through="Product_Member", related_name="product_members", blank=True
    )
    authorization_group_members: ManyToManyField = ManyToManyField(
        Authorization_Group,
        through="Product_Authorization_Group_Member",
        related_name="authorization_groups",
        blank=True,
    )

    apply_general_rules = BooleanField(default=True)

    notification_ms_teams_webhook = CharField(max_length=255, blank=True)
    notification_slack_webhook = CharField(max_length=255, blank=True)
    notification_email_to = CharField(max_length=255, blank=True)

    issue_tracker_active = BooleanField(default=False)
    issue_tracker_type = CharField(max_length=12, choices=Issue_Tracker.ISSUE_TRACKER_TYPE_CHOICES, blank=True)
    issue_tracker_base_url = CharField(max_length=255, blank=True)
    issue_tracker_username = CharField(max_length=255, blank=True)
    issue_tracker_api_key = CharField(max_length=255, blank=True)
    issue_tracker_project_id = CharField(max_length=255, blank=True)
    issue_tracker_labels = CharField(max_length=255, blank=True)
    issue_tracker_issue_type = CharField(max_length=255, blank=True)
    issue_tracker_status_closed = CharField(max_length=255, blank=True)
    issue_tracker_minimum_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)

    last_observation_change = DateTimeField(default=timezone.now)

    assessments_need_approval = BooleanField(default=False)
    new_observations_in_review = BooleanField(default=False)
    product_rules_need_approval = BooleanField(default=False)

    risk_acceptance_expiry_active = BooleanField(null=True)
    risk_acceptance_expiry_days = IntegerField(
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Days before risk acceptance expires, 0 means no expiry",
    )

    license_policy = ForeignKey(
        "licenses.License_Policy",
        on_delete=PROTECT,
        related_name="product",
        null=True,
        blank=True,
    )

    osv_enabled = BooleanField(default=True)
    osv_linux_distribution = CharField(
        max_length=12,
        choices=OSVLinuxDistribution.OSV_LINUX_DISTRIBUTION_CHOICES,
        blank=True,
    )
    osv_linux_release = CharField(max_length=255, blank=True)
    automatic_osv_scanning_enabled = BooleanField(default=False)

    has_cloud_resource = BooleanField(default=False)
    has_component = BooleanField(default=False)
    has_docker_image = BooleanField(default=False)
    has_endpoint = BooleanField(default=False)
    has_kubernetes_resource = BooleanField(default=False)
    has_source = BooleanField(default=False)
    has_potential_duplicates = BooleanField(default=False)

    class Meta:
        indexes = [
            Index(fields=["name"]),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.open_critical_observation_count: int | None = None
        self.open_high_observation_count: int | None = None
        self.open_medium_observation_count: int | None = None
        self.open_low_observation_count: int | None = None
        self.open_none_observation_count: int | None = None
        self.open_unknown_observation_count: int | None = None

        self.forbidden_licenses_count: int | None = None
        self.review_required_licenses_count: int | None = None
        self.unknown_licenses_count: int | None = None
        self.allowed_licenses_count: int | None = None
        self.ignored_licenses_count: int | None = None

        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Branch(Model, DirtyFieldsMixin):
    product = ForeignKey(Product, on_delete=CASCADE)
    name = CharField(max_length=255)
    is_default_branch = BooleanField(default=False)
    last_import = DateTimeField(null=True)
    housekeeping_protect = BooleanField(default=False)
    purl = CharField(max_length=255, blank=True)
    cpe23 = CharField(max_length=255, blank=True)
    osv_linux_distribution = CharField(
        max_length=12,
        choices=OSVLinuxDistribution.OSV_LINUX_DISTRIBUTION_CHOICES,
        blank=True,
    )
    osv_linux_release = CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (
            "product",
            "name",
        )
        indexes = [
            Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Service(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    name = CharField(max_length=255)

    class Meta:
        unique_together = (
            "product",
            "name",
        )
        indexes = [
            Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Product_Member(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    role = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = (
            "product",
            "user",
        )

    def __str__(self) -> str:
        return f"{self.product} / {self.user}"


class Product_Authorization_Group_Member(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    authorization_group = ForeignKey(Authorization_Group, on_delete=CASCADE)
    role = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = (
            "product",
            "authorization_group",
        )

    def __str__(self) -> str:
        return f"{self.product} / {self.authorization_group}"


class Observation(Model):
    product = ForeignKey(Product, on_delete=PROTECT)
    branch = ForeignKey(Branch, on_delete=CASCADE, null=True)
    parser = ForeignKey("import_observations.Parser", on_delete=PROTECT)
    title = CharField(max_length=255)
    description = TextField(max_length=2048, blank=True)
    recommendation = TextField(max_length=2048, blank=True)

    current_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES)
    numerical_severity = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    parser_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    rule_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    assessment_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)

    current_status = CharField(max_length=16, choices=Status.STATUS_CHOICES)
    parser_status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    vex_status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    rule_status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    assessment_status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)

    scanner_observation_id = CharField(max_length=255, blank=True)
    vulnerability_id = CharField(max_length=255, blank=True)
    vulnerability_id_aliases = CharField(max_length=512, blank=True)

    origin_component_name = CharField(max_length=255, blank=True)
    origin_component_version = CharField(max_length=255, blank=True)
    origin_component_name_version = CharField(max_length=513, blank=True)
    origin_component_purl = CharField(max_length=255, blank=True)
    origin_component_purl_type = CharField(max_length=16, blank=True)
    origin_component_cpe = CharField(max_length=255, blank=True)
    origin_component_dependencies = TextField(max_length=32768, blank=True)
    origin_component_cyclonedx_bom_link = CharField(max_length=512, blank=True)

    origin_docker_image_name = CharField(max_length=255, blank=True)
    origin_docker_image_tag = CharField(max_length=255, blank=True)
    origin_docker_image_name_tag = CharField(max_length=513, blank=True)
    origin_docker_image_name_tag_short = CharField(max_length=513, blank=True)
    origin_docker_image_digest = CharField(max_length=255, blank=True)

    origin_endpoint_url = TextField(max_length=2048, blank=True)
    origin_endpoint_scheme = CharField(max_length=255, blank=True)
    origin_endpoint_hostname = CharField(max_length=255, blank=True)
    origin_endpoint_port = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(65535)])
    origin_endpoint_path = TextField(max_length=2048, blank=True)
    origin_endpoint_params = TextField(max_length=2048, blank=True)
    origin_endpoint_query = TextField(max_length=2048, blank=True)
    origin_endpoint_fragment = TextField(max_length=2048, blank=True)

    origin_service_name = CharField(max_length=255, blank=True)
    origin_service = ForeignKey(Service, on_delete=PROTECT, null=True)

    origin_source_file = CharField(max_length=255, blank=True)
    origin_source_line_start = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])
    origin_source_line_end = IntegerField(null=True, validators=[MinValueValidator(0), MaxValueValidator(999999)])

    origin_source_file_link = CharField(max_length=2048, blank=True)

    origin_cloud_provider = CharField(max_length=255, blank=True)
    origin_cloud_account_subscription_project = CharField(max_length=255, blank=True)
    origin_cloud_resource = CharField(max_length=255, blank=True)
    origin_cloud_resource_type = CharField(max_length=255, blank=True)
    origin_cloud_qualified_resource = CharField(max_length=255, blank=True)

    origin_kubernetes_cluster = CharField(max_length=255, blank=True)
    origin_kubernetes_namespace = CharField(max_length=255, blank=True)
    origin_kubernetes_resource_type = CharField(max_length=255, blank=True)
    origin_kubernetes_resource_name = CharField(max_length=255, blank=True)
    origin_kubernetes_qualified_resource = CharField(max_length=255, blank=True)

    cvss3_score = DecimalField(max_digits=3, decimal_places=1, null=True)
    cvss3_vector = CharField(max_length=255, blank=True)
    cvss4_score = DecimalField(max_digits=3, decimal_places=1, null=True)
    cvss4_vector = CharField(max_length=255, blank=True)
    cve_found_in = CharField(max_length=255, blank=True)

    cwe = IntegerField(null=True, validators=[MinValueValidator(1), MaxValueValidator(999999)])

    epss_score = DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        validators=[MinValueValidator(Decimal(0)), MaxValueValidator(Decimal(100))],
    )
    epss_percentile = DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        validators=[MinValueValidator(Decimal(0)), MaxValueValidator(Decimal(100))],
    )

    found = DateField(null=True)
    scanner = CharField(max_length=255, blank=True)
    upload_filename = CharField(max_length=255, blank=True)
    api_configuration_name = CharField(max_length=255, blank=True)
    import_last_seen = DateTimeField()
    created = DateTimeField(auto_now_add=True)
    modified = DateTimeField(auto_now=True)
    last_observation_log = DateTimeField(default=timezone.now)
    identity_hash = CharField(max_length=64)

    general_rule = ForeignKey(
        "rules.Rule",
        related_name="general_rules",
        blank=True,
        null=True,
        on_delete=PROTECT,
    )
    product_rule = ForeignKey(
        "rules.Rule",
        related_name="product_rules",
        blank=True,
        null=True,
        on_delete=PROTECT,
    )

    issue_tracker_issue_id = CharField(max_length=255, blank=True)
    issue_tracker_issue_closed = BooleanField(default=False)
    issue_tracker_jira_initial_status = CharField(max_length=255, blank=True)

    has_potential_duplicates = BooleanField(default=False)

    current_vex_justification = CharField(
        max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True
    )
    parser_vex_justification = CharField(max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True)
    vex_vex_justification = CharField(max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True)
    rule_vex_justification = CharField(max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True)
    assessment_vex_justification = CharField(
        max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True
    )
    vex_statement = ForeignKey(
        "vex.VEX_Statement",
        related_name="vex_statements",
        blank=True,
        null=True,
        on_delete=SET_NULL,
    )

    risk_acceptance_expiry_date = DateField(null=True)

    class Meta:
        indexes = [
            Index(fields=["product", "branch"]),
            Index(fields=["title"]),
            Index(fields=["current_severity"]),
            Index(fields=["numerical_severity"]),
            Index(fields=["current_status"]),
            Index(fields=["vulnerability_id"]),
            Index(fields=["origin_component_name_version"]),
            Index(fields=["origin_component_cyclonedx_bom_link"]),
            Index(fields=["origin_docker_image_name_tag_short"]),
            Index(fields=["origin_service_name"]),
            Index(fields=["origin_endpoint_hostname"]),
            Index(fields=["origin_source_file"]),
            Index(fields=["origin_cloud_qualified_resource"]),
            Index(fields=["origin_kubernetes_qualified_resource"]),
            Index(fields=["last_observation_log"]),
            Index(fields=["epss_score"]),
            Index(fields=["scanner"]),
        ]

    def __str__(self) -> str:
        return f"{self.product} / {self.title}"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.unsaved_references: list[str] = []
        self.unsaved_evidences: list[list[str]] = []


class Observation_Log(Model):
    observation = ForeignKey(Observation, related_name="observation_logs", on_delete=CASCADE)
    user = ForeignKey("access_control.User", related_name="observation_logs", on_delete=PROTECT)
    severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    comment = TextField(max_length=4096)
    created = DateTimeField(auto_now_add=True)
    vex_justification = CharField(max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True)
    assessment_status = CharField(
        max_length=16,
        choices=Assessment_Status.ASSESSMENT_STATUS_CHOICES,
        default=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
    )
    approval_remark = TextField(max_length=255, blank=True)
    approval_date = DateTimeField(null=True)
    approval_user = ForeignKey(
        "access_control.User",
        related_name="observation_logs_approver",
        on_delete=PROTECT,
        null=True,
    )
    general_rule = ForeignKey(
        "rules.Rule",
        related_name="observation_log_general_rules",
        blank=True,
        null=True,
        on_delete=SET_NULL,
    )
    product_rule = ForeignKey(
        "rules.Rule",
        related_name="observation_log_product_rules",
        blank=True,
        null=True,
        on_delete=SET_NULL,
    )
    vex_statement = ForeignKey(
        "vex.VEX_Statement",
        related_name="observation_log_vex_statements",
        blank=True,
        null=True,
        on_delete=SET_NULL,
    )
    risk_acceptance_expiry_date = DateField(null=True)

    class Meta:
        indexes = [
            Index(fields=["observation", "-created"]),
            Index(fields=["-created"]),
        ]
        ordering = ["observation", "-created"]


class Evidence(Model):
    observation = ForeignKey(Observation, related_name="evidences", on_delete=CASCADE)
    name = CharField(max_length=255)
    evidence = TextField()

    class Meta:
        indexes = [
            Index(fields=["name"]),
        ]


class Reference(Model):
    observation = ForeignKey(Observation, related_name="references", on_delete=CASCADE)
    url = TextField(max_length=2048)


class Potential_Duplicate(Model):
    POTENTIAL_DUPLICATE_TYPE_COMPONENT = "Component"
    POTENTIAL_DUPLICATE_TYPE_SOURCE = "Source"

    POTENTIAL_DUPLICATE_TYPES = [
        (POTENTIAL_DUPLICATE_TYPE_COMPONENT, POTENTIAL_DUPLICATE_TYPE_COMPONENT),
        (POTENTIAL_DUPLICATE_TYPE_SOURCE, POTENTIAL_DUPLICATE_TYPE_SOURCE),
    ]

    observation = ForeignKey(Observation, related_name="potential_duplicates", on_delete=CASCADE)
    potential_duplicate_observation = ForeignKey(Observation, on_delete=CASCADE)
    type = CharField(max_length=12, choices=POTENTIAL_DUPLICATE_TYPES)

    class Meta:
        unique_together = (
            "observation",
            "potential_duplicate_observation",
        )


class Component(Model):
    id = CharField(max_length=32, primary_key=True)
    product = ForeignKey(Product, related_name="components", on_delete=DO_NOTHING)
    branch = ForeignKey(Branch, related_name="components", on_delete=DO_NOTHING, null=True)
    origin_service = ForeignKey(Service, on_delete=DO_NOTHING, null=True)
    component_name = CharField(max_length=255)
    component_version = CharField(max_length=255, blank=True)
    component_name_version = CharField(max_length=513, blank=True)
    component_purl = CharField(max_length=255, blank=True)
    component_purl_type = CharField(max_length=16, blank=True)
    component_cpe = CharField(max_length=255, blank=True)
    component_dependencies = TextField(max_length=32768, blank=True)
    component_cyclonedx_bom_link = CharField(max_length=512, blank=True)
    has_observations = BooleanField()

    class Meta:
        db_table = "core_component"
        managed = False
