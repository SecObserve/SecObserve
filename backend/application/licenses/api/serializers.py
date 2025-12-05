from typing import Optional

from django.core.validators import MinValueValidator
from license_expression import get_spdx_licensing
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from application.access_control.api.serializers import AuthorizationGroupListSerializer, UserListSerializer
from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import get_highest_user_role
from application.authorization.services.roles_permissions import Permissions, get_permissions_for_role
from application.commons.services.functions import get_comma_separated_as_list
from application.core.api.serializers_product import NestedProductSerializer, NestedProductSerializerSmall
from application.core.queries.product import get_products
from application.core.types import PURL_Type
from application.licenses.models import (
    Concluded_License,
    License,
    License_Component,
    License_Component_Evidence,
    License_Group,
    License_Group_Authorization_Group_Member,
    License_Group_Member,
    License_Policy,
    License_Policy_Authorization_Group_Member,
    License_Policy_Item,
    License_Policy_Member,
)
from application.licenses.queries.license_group_authorization_group_member import (
    get_license_group_authorization_group_member,
    get_license_group_authorization_group_members,
)
from application.licenses.queries.license_group_member import get_license_group_member, get_license_group_members
from application.licenses.queries.license_policy_authorization_group_member import (
    get_license_policy_authorization_group_member,
    get_license_policy_authorization_group_members,
)
from application.licenses.queries.license_policy_item import get_license_policy_items
from application.licenses.queries.license_policy_member import get_license_policy_member, get_license_policy_members


class LicenseSerializer(ModelSerializer):
    spdx_id_name = SerializerMethodField()
    is_in_license_group = SerializerMethodField()
    is_in_license_policy = SerializerMethodField()

    class Meta:
        model = License
        fields = "__all__"

    def get_spdx_id_name(self, obj: License) -> str:
        return f"{obj.spdx_id} / {obj.name}"

    def get_is_in_license_group(self, obj: License) -> bool:
        return License_Group.objects.filter(licenses=obj).exists()

    def get_is_in_license_policy(self, obj: License) -> bool:
        return License_Policy_Item.objects.filter(license=obj).exists()


class LicenseComponentEvidenceSerializer(ModelSerializer):
    product = SerializerMethodField()

    def get_product(self, evidence: License_Component_Evidence) -> int:
        return evidence.license_component.product.pk

    class Meta:
        model = License_Component_Evidence
        fields = "__all__"


class NestedLicenseComponentEvidenceSerializer(ModelSerializer):
    class Meta:
        model = License_Component_Evidence
        exclude = ["license_component", "evidence"]


class LicenseComponentSerializer(ModelSerializer):
    component_name_version_type = SerializerMethodField()
    branch_name = SerializerMethodField()
    origin_service_name = SerializerMethodField()
    license_policy_name: Optional[SerializerMethodField] = SerializerMethodField()
    license_policy_id: Optional[SerializerMethodField] = SerializerMethodField()
    evidences: Optional[NestedLicenseComponentEvidenceSerializer] = NestedLicenseComponentEvidenceSerializer(many=True)
    effective_license_type = SerializerMethodField()
    title = SerializerMethodField()
    permissions: Optional[SerializerMethodField] = SerializerMethodField()

    class Meta:
        model = License_Component
        fields = "__all__"

    def get_component_name_version_type(self, obj: License_Component) -> Optional[str]:
        if obj.component_name_version:
            component_name_version_type = obj.component_name_version
            if obj.component_purl_type:
                component_name_version_type += f" ({obj.component_purl_type})"
            return component_name_version_type

        return ""

    def get_branch_name(self, obj: License_Component) -> str:
        if obj.branch:
            return obj.branch.name

        return ""

    def get_origin_service_name(self, obj: License_Component) -> str:
        if obj.origin_service:
            return obj.origin_service.name

        return ""

    def get_license_policy_name(self, obj: License_Component) -> str:
        if obj.product.license_policy:
            return obj.product.license_policy.name

        if obj.product.product_group and obj.product.product_group.license_policy:
            return obj.product.product_group.license_policy.name

        return ""

    def get_license_policy_id(self, obj: License_Component) -> int:
        if obj.product.license_policy:
            return obj.product.license_policy.pk

        if obj.product.product_group and obj.product.product_group.license_policy:
            return obj.product.product_group.license_policy.pk

        return 0

    def get_effective_license_type(self, obj: License_Component) -> str:
        if obj.effective_spdx_license:
            return "SPDX"
        if obj.effective_license_expression:
            return "Expression"
        if obj.effective_non_spdx_license:
            return "Non-SPDX"
        return ""

    def get_title(self, obj: License_Component) -> str:
        return f"{obj.effective_license_name} / {obj.component_name_version}"

    def get_permissions(self, obj: License_Component) -> Optional[set[Permissions]]:
        return get_permissions_for_role(get_highest_user_role(obj.product))


class LicenseComponentListSerializer(LicenseComponentSerializer):
    license_policy_id = None
    license_policy_name = None
    evidences = None
    permissions = None

    class Meta:
        model = License_Component
        exclude = ["component_dependencies"]


class LicenseComponentIdSerializer(ModelSerializer):
    class Meta:
        model = License_Component
        fields = ["id"]


class LicenseComponentBulkDeleteSerializer(Serializer):
    components = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class LicenseComponentOverviewElementSerializer(Serializer):
    branch_name = CharField()
    effective_license_name = CharField()
    effective_license_type = CharField()
    evaluation_result = CharField()
    num_components = IntegerField()


class LicenseComponentOverviewSerializer(Serializer):
    count = IntegerField()
    results = ListField(child=LicenseComponentOverviewElementSerializer())


class ConcludedLicenseCreateUpdateSerializer(Serializer):
    manual_concluded_spdx_license = IntegerField(validators=[MinValueValidator(1)], required=False, allow_null=True)
    manual_concluded_non_spdx_license = CharField(max_length=255, required=False, allow_blank=True)
    manual_concluded_license_expression = CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        # check exactly one attribute is set
        if sum(1 for key in attrs if key.startswith("manual_concluded_") and attrs[key]) > 1:
            raise ValidationError("Only one concluded license field may be set.")

        return attrs


class ConcludedLicenseSerializer(ModelSerializer):
    product_data: NestedProductSerializer | NestedProductSerializerSmall = NestedProductSerializer(
        source="product", read_only=True
    )
    user_data = UserListSerializer(source="user", read_only=True)
    component_name_version = SerializerMethodField()
    manual_concluded_spdx_license_id = SerializerMethodField()

    def get_component_name_version(self, obj: Concluded_License) -> str:
        component_name_version = obj.component_name
        if obj.component_version:
            component_name_version += f":{obj.component_version}"
        if obj.component_purl_type:
            component_name_version += f" ({obj.component_purl_type})"
        return component_name_version

    def get_manual_concluded_spdx_license_id(self, obj: Concluded_License) -> str:
        if obj.manual_concluded_spdx_license:
            return obj.manual_concluded_spdx_license.spdx_id

        return ""

    class Meta:
        model = Concluded_License
        fields = "__all__"


class ConcludedLicenseListSerializer(ConcludedLicenseSerializer):
    product_data = NestedProductSerializerSmall(source="product", read_only=True)


class LicenseGroupSerializer(ModelSerializer):
    is_manager = SerializerMethodField()
    is_in_license_policy = SerializerMethodField()
    has_licenses = SerializerMethodField()
    has_users = SerializerMethodField()
    has_authorization_groups = SerializerMethodField()

    class Meta:
        model = License_Group
        exclude = ["licenses", "users", "authorization_groups"]

    def get_is_manager(self, obj: License_Group) -> bool:
        user = get_current_user()

        if License_Group_Member.objects.filter(license_group=obj, user=user, is_manager=True).exists():
            return True

        if License_Group_Authorization_Group_Member.objects.filter(
            license_group=obj, authorization_group__users=user, is_manager=True
        ).exists():
            return True

        return False

    def get_is_in_license_policy(self, obj: License_Group) -> bool:
        return get_license_policy_items().filter(license_group=obj).exists()

    def get_has_licenses(self, obj: License_Group) -> bool:
        return obj.licenses.exists()

    def get_has_users(self, obj: License_Group) -> bool:
        return get_license_group_members().filter(license_group=obj).exists()

    def get_has_authorization_groups(self, obj: License_Group) -> bool:
        return get_license_group_authorization_group_members().filter(license_group=obj).exists()


class LicenseGroupLicenseAddRemoveSerializer(Serializer):
    license = IntegerField(min_value=1, required=True)


class LicenseGroupAuthorizationGroupMemberSerializer(ModelSerializer):
    license_group_data = LicenseGroupSerializer(source="license_group", read_only=True)
    authorization_group_data = AuthorizationGroupListSerializer(source="authorization_group", read_only=True)

    class Meta:
        model = License_Group_Authorization_Group_Member
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        self.instance: License_Group_Authorization_Group_Member
        data_license_group: Optional[License_Group] = attrs.get("license_group")
        data_authorization_group = attrs.get("authorization_group")

        if self.instance is not None and (
            (data_license_group and data_license_group != self.instance.license_group)
            or (data_authorization_group and data_authorization_group != self.instance.authorization_group)
        ):
            raise ValidationError("License group and authorization group cannot be changed")

        if self.instance is None:
            if data_license_group is None:
                raise ValidationError("License group is required")
            if data_authorization_group is None:
                raise ValidationError("Authorization group is required")

            license_group_authorization_group_member = get_license_group_authorization_group_member(
                data_license_group, data_authorization_group
            )
            if license_group_authorization_group_member:
                raise ValidationError(
                    "License group authorization group member "
                    + f"{data_license_group} / {data_authorization_group} already exists"
                )

        return attrs


class LicenseGroupMemberSerializer(ModelSerializer):
    license_group_data = LicenseGroupSerializer(source="license_group", read_only=True)
    user_data = UserListSerializer(source="user", read_only=True)

    class Meta:
        model = License_Group_Member
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        self.instance: License_Group_Member
        data_license_group: Optional[License_Group] = attrs.get("license_group")
        data_user = attrs.get("user")

        if self.instance is not None and (
            (data_license_group and data_license_group != self.instance.license_group)
            or (data_user and data_user != self.instance.user)
        ):
            raise ValidationError("License group and user cannot be changed")

        if self.instance is None:
            if data_license_group is None:
                raise ValidationError("License group is required")
            if data_user is None:
                raise ValidationError("User is required")

            license_group_member = get_license_group_member(data_license_group, data_user)
            if license_group_member:
                raise ValidationError(f"License group member {data_license_group} / {data_user} already exists")

        return attrs


class LicenseGroupCopySerializer(Serializer):
    name = CharField(max_length=255, required=True)


class LicensePolicySerializer(ModelSerializer):
    parent_name = SerializerMethodField()
    is_parent = SerializerMethodField()
    is_manager = SerializerMethodField()
    has_products = SerializerMethodField()
    has_product_groups = SerializerMethodField()
    has_items = SerializerMethodField()
    has_users = SerializerMethodField()
    has_authorization_groups = SerializerMethodField()

    def get_parent_name(self, obj: License_Policy) -> str:
        if obj.parent:
            return obj.parent.name

        return ""

    def get_is_parent(self, obj: License_Policy) -> bool:
        return obj.children.exists()

    def get_is_manager(self, obj: License_Policy) -> bool:
        user = get_current_user()

        if License_Policy_Member.objects.filter(license_policy=obj, user=user, is_manager=True).exists():
            return True

        if License_Policy_Authorization_Group_Member.objects.filter(
            license_policy=obj, authorization_group__users=user, is_manager=True
        ).exists():
            return True

        return False

    def get_has_products(self, obj: License_Policy) -> bool:
        return get_products(is_product_group=False).filter(license_policy=obj).exists()

    def get_has_product_groups(self, obj: License_Policy) -> bool:
        return get_products(is_product_group=True).filter(license_policy=obj).exists()

    def get_has_items(self, obj: License_Policy) -> bool:
        return obj.license_policy_items.exists()

    def get_has_users(self, obj: License_Policy) -> bool:
        return get_license_policy_members().filter(license_policy=obj).exists()

    def get_has_authorization_groups(self, obj: License_Policy) -> bool:
        return get_license_policy_authorization_group_members().filter(license_policy=obj).exists()

    class Meta:
        model = License_Policy
        exclude = ["users", "authorization_groups"]

    def validate_ignore_component_types(self, value: str) -> str:
        ignore_component_types = get_comma_separated_as_list(value)
        for component_type in ignore_component_types:
            for component_type in ignore_component_types:
                if not PURL_Type.PURL_TYPE_CHOICES.get(component_type):
                    raise ValidationError(f"Invalid component type {component_type}")

        return value

    def validate_parent(self, value: License_Policy) -> License_Policy:
        if value and value.parent:
            raise ValidationError("A child cannot be a parent itself")

        return value

    def update(self, instance: License_Policy, validated_data: dict) -> License_Policy:
        parent = validated_data.get("parent")
        instance_has_children = instance.children.exists()
        if parent:
            if instance_has_children:
                raise ValidationError("A parent cannot have a parent itself")
            if instance == parent:
                raise ValidationError("A license policy cannot be parent of itself")

        return super().update(instance, validated_data)


class LicensePolicyItemSerializer(ModelSerializer):
    license_spdx_id = SerializerMethodField()
    license_group_name = SerializerMethodField()
    license_policy_data = LicensePolicySerializer(source="license_policy", read_only=True)

    class Meta:
        model = License_Policy_Item
        exclude = ["numerical_evaluation_result"]

    def get_license_spdx_id(self, obj: License_Policy_Item) -> str:
        if obj.license:
            return obj.license.spdx_id

        return ""

    def get_license_group_name(self, obj: License_Policy_Item) -> str:
        if obj.license_group:
            return obj.license_group.name

        return ""

    def validate(self, attrs: dict) -> dict:
        self.instance: License_Policy_Item
        data_license_group = attrs.get("license_group")
        data_license = attrs.get("license")
        data_license_expression = attrs.get("license_expression", "")
        data_non_spdx_license = attrs.get("non_spdx_license", "")

        if self.instance:
            self.instance.license_group = data_license_group
            self.instance.license = data_license
            self.instance.license_expression = data_license_expression
            self.instance.non_spdx_license = data_non_spdx_license
            num_fields = (
                bool(self.instance.license_group)
                + bool(self.instance.license)
                + bool(self.instance.license_expression)
                + bool(self.instance.non_spdx_license)
            )
            try:
                item = License_Policy_Item.objects.get(
                    license_policy=self.instance.license_policy,
                    license_group=self.instance.license_group,
                    license=self.instance.license,
                    license_expression=self.instance.license_expression,
                    non_spdx_license=self.instance.non_spdx_license,
                )
                if item.pk != self.instance.pk:
                    raise ValidationError("License policy item already exists")
            except License_Policy_Item.DoesNotExist:
                pass
        else:
            num_fields = (
                bool(data_license_group)
                + bool(data_license)
                + bool(data_license_expression)
                + bool(data_non_spdx_license)
            )
            try:
                License_Policy_Item.objects.get(
                    license_policy=attrs.get("license_policy"),
                    license_group=data_license_group,
                    license=data_license,
                    license_expression=data_license_expression,
                    non_spdx_license=data_non_spdx_license,
                )
                raise ValidationError("License policy item already exists")
            except License_Policy_Item.DoesNotExist:
                pass

        if num_fields == 0:
            raise ValidationError("One of license group, license, license expression or unknown license must be set")
        if num_fields > 1:
            raise ValidationError(
                "Only one of license group, license, license expression or unknown license must be set"
            )
        return attrs

    def validate_license_expression(self, value: str) -> str:
        if value:
            licensing = get_spdx_licensing()
            expression_info = licensing.validate(value, strict=True)
            if not expression_info.errors:
                value = expression_info.normalized_expression
            else:
                raise ValidationError(f"Invalid license expression: {expression_info.errors}")

        return value


class LicensePolicyMemberSerializer(ModelSerializer):
    license_policy_data = LicensePolicySerializer(source="license_policy", read_only=True)
    user_data = UserListSerializer(source="user", read_only=True)

    class Meta:
        model = License_Policy_Member
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        self.instance: License_Policy_Member
        data_license_policy: Optional[License_Policy] = attrs.get("license_policy")
        data_user = attrs.get("user")

        if self.instance is not None and (
            (data_license_policy and data_license_policy != self.instance.license_policy)
            or (data_user and data_user != self.instance.user)
        ):
            raise ValidationError("License policy and user cannot be changed")

        if self.instance is None:
            if data_license_policy is None:
                raise ValidationError("License policy is required")
            if data_user is None:
                raise ValidationError("User is required")

            license_group_member = get_license_policy_member(data_license_policy, data_user)
            if license_group_member:
                raise ValidationError(f"License policy member {data_license_policy} / {data_user} already exists")

        return attrs


class LicensePolicyAuthorizationGroupMemberSerializer(ModelSerializer):
    license_policy_data = LicensePolicySerializer(source="license_policy", read_only=True)
    authorization_group_data = AuthorizationGroupListSerializer(source="authorization_group", read_only=True)

    class Meta:
        model = License_Policy_Authorization_Group_Member
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        self.instance: License_Policy_Authorization_Group_Member
        data_license_policy: Optional[License_Policy] = attrs.get("license_policy")
        data_authorization_group = attrs.get("authorization_group")

        if self.instance is not None and (
            (data_license_policy and data_license_policy != self.instance.license_policy)
            or (data_authorization_group and data_authorization_group != self.instance.authorization_group)
        ):
            raise ValidationError("License policy and authorization group cannot be changed")

        if self.instance is None:
            if data_license_policy is None:
                raise ValidationError("License policy is required")
            if data_authorization_group is None:
                raise ValidationError("Authorization group is required")

            license_policy_authorization_group_member = get_license_policy_authorization_group_member(
                data_license_policy, data_authorization_group
            )
            if license_policy_authorization_group_member:
                raise ValidationError(
                    "License policy authorization group member "
                    + f"{data_license_policy} / {data_authorization_group} already exists"
                )

        return attrs


class LicensePolicyCopySerializer(Serializer):
    name = CharField(max_length=255, required=True)
