from datetime import date
from typing import Optional

from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework.serializers import (
    CharField,
    DateField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from application.access_control.api.serializers import (
    NestedAuthorizationGroupSerializer,
    UserListSerializer,
)
from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import get_highest_user_role
from application.authorization.services.roles_permissions import (
    Permissions,
    Roles,
    get_permissions_for_role,
)
from application.commons.models import Settings
from application.core.api.serializers_helpers import (
    validate_cpe23,
    validate_purl,
    validate_url,
)
from application.core.models import (
    Branch,
    Observation,
    Observation_Log,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
    Service,
)
from application.core.queries.product_member import (
    get_product_authorization_group_member,
    get_product_member,
)
from application.core.services.risk_acceptance_expiry import (
    calculate_risk_acceptance_expiry_date,
)
from application.core.types import Assessment_Status, Status
from application.import_observations.models import Api_Configuration
from application.issue_tracker.types import Issue_Tracker
from application.licenses.models import License_Component
from application.rules.models import Rule
from application.rules.types import Rule_Status


class ProductCoreSerializer(ModelSerializer):
    permissions = SerializerMethodField()

    def get_permissions(self, obj: Product) -> Optional[set[Permissions]]:
        return get_permissions_for_role(get_highest_user_role(obj))

    class Meta:
        model = Product
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        settings = Settings.load()

        if attrs.get("repository_branch_housekeeping_active") is True:
            if not attrs.get("repository_branch_housekeeping_keep_inactive_days"):
                attrs["repository_branch_housekeeping_keep_inactive_days"] = (
                    settings.branch_housekeeping_keep_inactive_days
                )

        if attrs.get("repository_branch_housekeeping_active") is False:
            attrs["repository_branch_housekeeping_keep_inactive_days"] = None
            attrs["repository_branch_housekeeping_exempt_branches"] = ""

        if attrs.get("security_gate_active") is True:
            if not attrs.get("security_gate_threshold_critical"):
                attrs["security_gate_threshold_critical"] = settings.security_gate_threshold_critical
            if not attrs.get("security_gate_threshold_high"):
                attrs["security_gate_threshold_high"] = settings.security_gate_threshold_high
            if not attrs.get("security_gate_threshold_medium"):
                attrs["security_gate_threshold_medium"] = settings.security_gate_threshold_medium
            if not attrs.get("security_gate_threshold_low"):
                attrs["security_gate_threshold_low"] = settings.security_gate_threshold_low
            if not attrs.get("security_gate_threshold_none"):
                attrs["security_gate_threshold_none"] = settings.security_gate_threshold_none
            if not attrs.get("security_gate_threshold_unknown"):
                attrs["security_gate_threshold_unknown"] = settings.security_gate_threshold_unknown

        if attrs.get("security_gate_active") is False:
            attrs["security_gate_threshold_critical"] = None
            attrs["security_gate_threshold_high"] = None
            attrs["security_gate_threshold_medium"] = None
            attrs["security_gate_threshold_low"] = None
            attrs["security_gate_threshold_none"] = None
            attrs["security_gate_threshold_unknown"] = None

        return super().validate(attrs)


class ProductGroupSerializer(ProductCoreSerializer):
    open_critical_observation_count = IntegerField(read_only=True)
    open_high_observation_count = IntegerField(read_only=True)
    open_medium_observation_count = IntegerField(read_only=True)
    open_low_observation_count = IntegerField(read_only=True)
    open_none_observation_count = IntegerField(read_only=True)
    open_unknown_observation_count = IntegerField(read_only=True)
    forbidden_licenses_count = IntegerField(read_only=True)
    review_required_licenses_count = IntegerField(read_only=True)
    unknown_licenses_count = IntegerField(read_only=True)
    allowed_licenses_count = IntegerField(read_only=True)
    ignored_licenses_count = IntegerField(read_only=True)

    products_count = SerializerMethodField()
    product_rule_approvals = SerializerMethodField()

    def get_products_count(self, obj: Product) -> int:
        return obj.products.count()

    def get_product_rule_approvals(self, obj: Product) -> int:
        if not obj.product_rules_need_approval:
            return 0

        return Rule.objects.filter(product=obj, approval_status=Rule_Status.RULE_STATUS_NEEDS_APPROVAL).count()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "products_count",
            "permissions",
            "open_critical_observation_count",
            "open_high_observation_count",
            "open_medium_observation_count",
            "open_low_observation_count",
            "open_none_observation_count",
            "open_unknown_observation_count",
            "repository_branch_housekeeping_active",
            "repository_branch_housekeeping_keep_inactive_days",
            "repository_branch_housekeeping_exempt_branches",
            "notification_ms_teams_webhook",
            "notification_slack_webhook",
            "notification_email_to",
            "security_gate_active",
            "security_gate_threshold_critical",
            "security_gate_threshold_high",
            "security_gate_threshold_medium",
            "security_gate_threshold_low",
            "security_gate_threshold_none",
            "security_gate_threshold_unknown",
            "assessments_need_approval",
            "product_rules_need_approval",
            "risk_acceptance_expiry_active",
            "risk_acceptance_expiry_days",
            "new_observations_in_review",
            "product_rule_approvals",
            "license_policy",
            "forbidden_licenses_count",
            "review_required_licenses_count",
            "unknown_licenses_count",
            "allowed_licenses_count",
            "ignored_licenses_count",
        ]

    def create(self, validated_data: dict) -> Product:
        product_group = super().create(validated_data)
        product_group.is_product_group = True
        product_group.save()
        return product_group

    def update(self, instance: Product, validated_data: dict) -> Product:
        product_group = super().update(instance, validated_data)
        if product_group.is_product_group is False:
            product_group.is_product_group = True
            product_group.save()
        return product_group


class ProductNameSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name"]


class ProductListSerializer(ProductCoreSerializer):
    open_critical_observation_count = IntegerField(read_only=True)
    open_high_observation_count = IntegerField(read_only=True)
    open_medium_observation_count = IntegerField(read_only=True)
    open_low_observation_count = IntegerField(read_only=True)
    open_none_observation_count = IntegerField(read_only=True)
    open_unknown_observation_count = IntegerField(read_only=True)
    forbidden_licenses_count = IntegerField(read_only=True)
    review_required_licenses_count = IntegerField(read_only=True)
    unknown_licenses_count = IntegerField(read_only=True)
    allowed_licenses_count = IntegerField(read_only=True)
    ignored_licenses_count = IntegerField(read_only=True)

    product_group_name = SerializerMethodField()
    repository_default_branch_name = SerializerMethodField()

    class Meta:
        model = Product
        exclude = ["is_product_group", "members", "authorization_group_members"]

    def get_product_group_name(self, obj: Product) -> str:
        if not obj.product_group:
            return ""
        return obj.product_group.name

    def get_repository_default_branch_name(self, obj: Product) -> str:
        if not obj.repository_default_branch:
            return ""
        return obj.repository_default_branch.name


class ProductSerializer(ProductListSerializer):  # pylint: disable=too-many-public-methods
    # all these methods are needed
    product_group_repository_branch_housekeeping_active = SerializerMethodField()
    product_group_security_gate_active = SerializerMethodField()
    product_group_assessments_need_approval = SerializerMethodField()
    observation_reviews = SerializerMethodField()
    observation_log_approvals = SerializerMethodField()
    has_services = SerializerMethodField()
    product_group_product_rules_need_approval = SerializerMethodField()
    product_rule_approvals = SerializerMethodField()
    risk_acceptance_expiry_date_calculated = SerializerMethodField()
    product_group_new_observations_in_review = SerializerMethodField()
    has_branches = SerializerMethodField()
    has_licenses = SerializerMethodField()
    product_group_license_policy = SerializerMethodField()
    has_api_configurations = SerializerMethodField()
    has_branch_purls = SerializerMethodField()
    has_branch_cpe23s = SerializerMethodField()
    has_branch_osv_linux_distribution = SerializerMethodField()
    has_concluded_comments = SerializerMethodField()

    class Meta:
        model = Product
        read_only_fields = ["repository_default_branch"]
        exclude = ["is_product_group", "members", "authorization_group_members"]

    def get_product_group_repository_branch_housekeeping_active(self, obj: Product) -> Optional[bool]:
        if not obj.product_group:
            return None
        return obj.product_group.repository_branch_housekeeping_active

    def get_product_group_security_gate_active(self, obj: Product) -> Optional[bool]:
        if not obj.product_group:
            return None
        return obj.product_group.security_gate_active

    def get_product_group_assessments_need_approval(self, obj: Product) -> bool:
        if not obj.product_group:
            return False
        return obj.product_group.assessments_need_approval

    def get_observation_reviews(self, obj: Product) -> int:
        return Observation.objects.filter(product=obj, current_status=Status.STATUS_IN_REVIEW).count()

    def get_observation_log_approvals(self, obj: Product) -> int:
        if obj.product_group:
            if not obj.product_group.assessments_need_approval and not obj.assessments_need_approval:
                return 0
        else:
            if not obj.assessments_need_approval:
                return 0

        return Observation_Log.objects.filter(
            observation__product=obj,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
        ).count()

    def get_has_services(self, obj: Product) -> bool:
        return Service.objects.filter(product=obj).exists()

    def get_product_group_product_rules_need_approval(self, obj: Product) -> bool:
        if not obj.product_group:
            return False
        return obj.product_group.product_rules_need_approval

    def get_product_rule_approvals(self, obj: Product) -> int:
        if obj.product_group:
            if not obj.product_group.product_rules_need_approval and not obj.product_rules_need_approval:
                return 0
        else:
            if not obj.product_rules_need_approval:
                return 0

        return Rule.objects.filter(product=obj, approval_status=Rule_Status.RULE_STATUS_NEEDS_APPROVAL).count()

    def get_risk_acceptance_expiry_date_calculated(self, obj: Product) -> Optional[date]:
        return calculate_risk_acceptance_expiry_date(obj)

    def get_product_group_new_observations_in_review(self, obj: Product) -> bool:
        if not obj.product_group:
            return False
        return obj.product_group.new_observations_in_review

    def get_has_branches(self, obj: Product) -> bool:
        return Branch.objects.filter(product=obj).exists()

    def get_has_licenses(self, obj: Product) -> bool:
        return License_Component.objects.filter(product=obj).exists()

    def get_product_group_license_policy(self, obj: Product) -> Optional[int]:
        if not obj.product_group or not obj.product_group.license_policy:
            return None
        return obj.product_group.license_policy.id

    def get_has_api_configurations(self, obj: Product) -> bool:
        return Api_Configuration.objects.filter(product=obj).exists()

    def get_has_branch_purls(self, obj: Product) -> bool:
        return Branch.objects.filter(product=obj).exclude(purl="").exists()

    def get_has_branch_cpe23s(self, obj: Product) -> bool:
        return Branch.objects.filter(product=obj).exclude(cpe23="").exists()

    def get_has_branch_osv_linux_distribution(self, obj: Product) -> bool:
        return Branch.objects.filter(product=obj).exclude(osv_linux_distribution="").exists()

    def get_has_concluded_comments(self, obj: Product) -> bool:
        return License_Component.objects.filter(product=obj).exclude(manual_concluded_comment="").exists()

    def validate(self, attrs: dict) -> dict:  # pylint: disable=too-many-branches
        # There are quite a lot of branches, but at least they are not nested too much
        if attrs.get("issue_tracker_type") == Issue_Tracker.ISSUE_TRACKER_GITHUB:
            attrs["issue_tracker_base_url"] = "https://api.github.com"

        if not (
            attrs.get("issue_tracker_type")
            and attrs.get("issue_tracker_base_url")
            and attrs.get("issue_tracker_api_key")
            and attrs.get("issue_tracker_project_id")
        ) and not (
            not attrs.get("issue_tracker_type")
            and not attrs.get("issue_tracker_base_url")
            and not attrs.get("issue_tracker_api_key")
            and not attrs.get("issue_tracker_project_id")
        ):
            raise ValidationError("Either all or none of the issue tracker fields must be set")

        if attrs.get("issue_tracker_active") and not attrs.get("issue_tracker_type"):
            raise ValidationError("Issue tracker data must be set when issue tracking is active")

        if attrs.get("issue_tracker_type") == Issue_Tracker.ISSUE_TRACKER_JIRA:
            if not attrs.get("issue_tracker_username"):
                raise ValidationError("Username must be set when issue tracker type is Jira")
            if not attrs.get("issue_tracker_issue_type"):
                raise ValidationError("Issue type must be set when issue tracker type is Jira")
            if not attrs.get("issue_tracker_status_closed"):
                raise ValidationError("Closed status must be set when issue tracker type is Jira")

        if attrs.get("issue_tracker_type") and attrs.get("issue_tracker_type") != Issue_Tracker.ISSUE_TRACKER_JIRA:
            if attrs.get("issue_tracker_username"):
                raise ValidationError("Username must not be set when issue tracker type is not Jira")
            if attrs.get("issue_tracker_issue_type"):
                raise ValidationError("Isse type must not be set when issue tracker type is not Jira")
            if attrs.get("issue_tracker_status_closed"):
                raise ValidationError("Closed status must not be set when issue tracker type is not Jira")

        if attrs.get("osv_linux_release") and not attrs.get("osv_linux_distribution"):
            raise ValidationError("osv_linux_release cannot be set without osv_linux_distribution")

        return super().validate(attrs)

    def validate_product_group(self, product: Product) -> Product:
        if product and product.is_product_group is False:
            raise ValidationError("Product group must be a product group")

        return product

    def validate_repository_prefix(self, repository_prefix: str) -> str:
        return validate_url(repository_prefix)

    def validate_notification_ms_teams_webhook(self, repository_prefix: str) -> str:
        return validate_url(repository_prefix)

    def validate_notification_slack_webhook(self, repository_prefix: str) -> str:
        return validate_url(repository_prefix)

    def validate_purl(self, purl: str) -> str:
        return validate_purl(purl)

    def validate_cpe23(self, cpe23: str) -> str:
        return validate_cpe23(cpe23)


class NestedProductSerializer(ModelSerializer):
    permissions = SerializerMethodField()
    product_group_assessments_need_approval = SerializerMethodField()
    product_group_product_rules_need_approval = SerializerMethodField()
    risk_acceptance_expiry_date_calculated = SerializerMethodField()

    class Meta:
        model = Product
        exclude = ["members", "authorization_group_members"]

    def get_permissions(self, product: Product) -> Optional[set[Permissions]]:
        return get_permissions_for_role(get_highest_user_role(product))

    def get_product_group_assessments_need_approval(self, obj: Product) -> bool:
        if not obj.product_group:
            return False
        return obj.product_group.assessments_need_approval

    def get_product_group_product_rules_need_approval(self, obj: Product) -> bool:
        if not obj.product_group:
            return False
        return obj.product_group.product_rules_need_approval

    def get_risk_acceptance_expiry_date_calculated(self, obj: Product) -> Optional[date]:
        return calculate_risk_acceptance_expiry_date(obj)


class NestedProductSerializerSmall(ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "is_product_group"]


class NestedProductListSerializer(ModelSerializer):
    product_group_name = SerializerMethodField()

    class Meta:
        model = Product
        exclude = [
            "members",
            "authorization_group_members",
            "is_product_group",
            "new_observations_in_review",
        ]

    def get_product_group_name(self, obj: Product) -> str:
        if not obj.product_group:
            return ""
        return obj.product_group.name


class ProductMemberSerializer(ModelSerializer):
    user_data = UserListSerializer(source="user", read_only=True)
    product_data = NestedProductSerializerSmall(source="product", read_only=True)

    class Meta:
        model = Product_Member
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        self.instance: Product_Member
        data_product: Optional[Product] = attrs.get("product")
        data_user = attrs.get("user")

        current_user = get_current_user()

        if self.instance is None:
            if data_product is None:
                raise ValidationError("Product must be set")
            if data_user is None:
                raise ValidationError("User must be set")

            product_member = get_product_member(data_product, data_user)
            if product_member:
                raise ValidationError(f"Product member {data_product} / {data_user} already exists")

            highest_user_role = get_highest_user_role(data_product, current_user)
        else:
            if (data_product and data_product != self.instance.product) or (
                data_user and data_user != self.instance.user
            ):
                raise ValidationError("Product and user cannot be changed")

            highest_user_role = get_highest_user_role(self.instance.product, current_user)

        if highest_user_role != Roles.Owner and not (current_user and current_user.is_superuser):
            if attrs.get("role") == Roles.Owner:
                raise ValidationError("You are not permitted to add a member as Owner")
            if attrs.get("role") != Roles.Owner and self.instance is not None and self.instance.role == Roles.Owner:
                raise ValidationError("You are not permitted to change the Owner role")

        return attrs


class ProductAuthorizationGroupMemberSerializer(ModelSerializer):
    authorization_group_data = NestedAuthorizationGroupSerializer(source="authorization_group", read_only=True)
    product_data = NestedProductSerializerSmall(source="product", read_only=True)

    class Meta:
        model = Product_Authorization_Group_Member
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        self.instance: Product_Authorization_Group_Member
        data_product: Optional[Product] = attrs.get("product")
        data_authorization_group = attrs.get("authorization_group")

        current_user = get_current_user()

        if self.instance is None:
            if data_product is None:
                raise ValidationError("Product must be set")
            if data_authorization_group is None:
                raise ValidationError("Authorization group must be set")

            product_authorization_group_member = get_product_authorization_group_member(
                data_product, data_authorization_group
            )
            if product_authorization_group_member:
                raise ValidationError(
                    f"Product authorization group member {data_product} / {data_authorization_group} already exists"
                )
            highest_user_role = get_highest_user_role(data_product, current_user)
        else:
            if (data_product and data_product != self.instance.product) or (
                data_authorization_group and data_authorization_group != self.instance.authorization_group
            ):
                raise ValidationError("Product and authorization group cannot be changed")
            highest_user_role = get_highest_user_role(self.instance.product, current_user)

        if highest_user_role != Roles.Owner and not (current_user and current_user.is_superuser):
            if attrs.get("role") == Roles.Owner:
                raise ValidationError("You are not permitted to add a member as Owner")
            if attrs.get("role") != Roles.Owner and self.instance is not None and self.instance.role == Roles.Owner:
                raise ValidationError("You are not permitted to change the Owner role")

        return attrs


class ProductApiTokenSerializer(Serializer):
    id = IntegerField(read_only=True)
    product = IntegerField(validators=[MinValueValidator(1)])
    role = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    name = CharField(max_length=32)
    expiration_date = DateField(required=False, allow_null=True)


class BranchSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()
    open_critical_observation_count = IntegerField(read_only=True)
    open_high_observation_count = IntegerField(read_only=True)
    open_medium_observation_count = IntegerField(read_only=True)
    open_low_observation_count = IntegerField(read_only=True)
    open_none_observation_count = IntegerField(read_only=True)
    open_unknown_observation_count = IntegerField(read_only=True)
    forbidden_licenses_count = IntegerField(read_only=True)
    review_required_licenses_count = IntegerField(read_only=True)
    unknown_licenses_count = IntegerField(read_only=True)
    allowed_licenses_count = IntegerField(read_only=True)
    ignored_licenses_count = IntegerField(read_only=True)

    def validate_purl(self, purl: str) -> str:
        return validate_purl(purl)

    def validate_cpe23(self, cpe23: str) -> str:
        return validate_cpe23(cpe23)

    def get_name_with_product(self, obj: Service) -> str:
        return f"{obj.name} ({obj.product.name})"

    class Meta:
        model = Branch
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:  # pylint: disable=too-many-branches
        if attrs.get("osv_linux_release") and not attrs.get("osv_linux_distribution"):
            raise ValidationError("osv_linux_release cannot be set without osv_linux_distribution")

        return super().validate(attrs)


class BranchNameSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "name", "name_with_product"]

    def get_name_with_product(self, obj: Branch) -> str:
        return f"{obj.name} ({obj.product.name})"


class ServiceSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()
    open_critical_observation_count = IntegerField(read_only=True)
    open_high_observation_count = IntegerField(read_only=True)
    open_medium_observation_count = IntegerField(read_only=True)
    open_low_observation_count = IntegerField(read_only=True)
    open_none_observation_count = IntegerField(read_only=True)
    open_unknown_observation_count = IntegerField(read_only=True)
    forbidden_licenses_count = IntegerField(read_only=True)
    review_required_licenses_count = IntegerField(read_only=True)
    unknown_licenses_count = IntegerField(read_only=True)
    allowed_licenses_count = IntegerField(read_only=True)
    ignored_licenses_count = IntegerField(read_only=True)

    class Meta:
        model = Service
        fields = "__all__"

    def get_name_with_product(self, obj: Service) -> str:
        return f"{obj.name} ({obj.product.name})"


class ServiceNameSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "name", "name_with_product"]

    def get_name_with_product(self, obj: Service) -> str:
        return f"{obj.name} ({obj.product.name})"


class PURLTypeElementSerializer(Serializer):
    id = CharField()
    name = CharField()


class PURLTypeSerializer(Serializer):
    count = IntegerField()
    results = ListField(child=PURLTypeElementSerializer())
