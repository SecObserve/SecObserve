from datetime import timedelta
from typing import Any

from django.db.models import QuerySet
from django.utils import timezone
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
    NumberFilter,
    OrderingFilter,
)

from application.commons.api.extended_ordering_filter import ExtendedOrderingFilter
from application.commons.types import Age_Choices
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
from application.licenses.queries.license_group import get_license_groups


class ConcludedLicenseFilter(FilterSet):
    component_name = CharFilter(field_name="component_name", lookup_expr="icontains")
    component_version = CharFilter(field_name="component_version", lookup_expr="icontains")
    manual_concluded_license_expression = CharFilter(
        field_name="manual_concluded_license_expression", lookup_expr="icontains"
    )
    manual_concluded_non_spdx_license = CharFilter(
        field_name="manual_concluded_non_spdx_license", lookup_expr="icontains"
    )
    age = ChoiceFilter(field_name="age", method="get_age", choices=Age_Choices.AGE_CHOICES)

    def get_age(self, queryset: QuerySet, name: Any, value: Any) -> QuerySet:  # pylint: disable=unused-argument
        days = Age_Choices.get_days_from_age(value)

        if days is None:
            return queryset

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_threshold = today - timedelta(days=int(days))
        return queryset.filter(last_updated__gte=time_threshold)

    ordering = ExtendedOrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("product__name", "product_data.name"),
            (("component_name", "component_version", "component_purl_type"), "component_name_version"),
            ("manual_concluded_spdx_license__spdx_id", "manual_concluded_spdx_license_id"),
            ("manual_concluded_license_expression", "manual_concluded_license_expression"),
            ("manual_concluded_non_spdx_license", "manual_concluded_non_spdx_license"),
            ("user__full_name", "user_data.full_name"),
            ("last_updated", "last_updated"),
        )
    )

    class Meta:
        model = Concluded_License
        fields = "__all__"


class LicenseComponentFilter(FilterSet):
    component_name_version = CharFilter(field_name="component_name_version", lookup_expr="icontains")
    effective_license_name = CharFilter(field_name="effective_license_name", lookup_expr="icontains")
    effective_license_name_exact = CharFilter(field_name="effective_license_name")
    effective_license_spdx_id = CharFilter(field_name="effective_spdx_license__spdx_id", lookup_expr="icontains")
    effective_license_expression = CharFilter(field_name="effective_license_expression", lookup_expr="icontains")
    effective_non_spdx_license = CharFilter(field_name="effective_non_spdx_license", lookup_expr="icontains")
    age = ChoiceFilter(field_name="age", method="get_age", choices=Age_Choices.AGE_CHOICES)
    branch_name_exact = CharFilter(field_name="branch__name")
    manual_concluded_comment = CharFilter(field_name="manual_concluded_comment", lookup_expr="icontains")

    def get_age(self, queryset: QuerySet, name: Any, value: Any) -> QuerySet:  # pylint: disable=unused-argument
        days = Age_Choices.get_days_from_age(value)

        if days is None:
            return queryset

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_threshold = today - timedelta(days=int(days))
        return queryset.filter(last_change__gte=time_threshold)

    ordering = ExtendedOrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("effective_spdx_license__spdx_id", "license_data.spdx_id"),
            ("effective_license_expression", "effective_license_expression"),
            ("effective_non_spdx_license", "effective_non_spdx_license"),
            (
                ("effective_license_name", "numerical_evaluation_result", "component_name_version"),
                "effective_license_name",
            ),
            (("numerical_evaluation_result", "effective_license_name", "component_name_version"), "evaluation_result"),
            (
                ("branch__name", "effective_license_name", "numerical_evaluation_result", "component_name_version"),
                "branch_name",
            ),
            ("component_name_version", "component_name_version"),
            ("component_name_version", "component_name_version_type"),
            (
                (
                    "component_purl_type",
                    "numerical_evaluation_result",
                    "effective_license_name",
                    "component_name_version",
                ),
                "component_purl_type",
            ),
            (
                (
                    "origin_service__name",
                    "effective_license_name",
                    "numerical_evaluation_result",
                    "component_name_version",
                ),
                "origin_service_name",
            ),
            (
                (
                    "manual_concluded_comment",
                    "effective_license_name",
                    "numerical_evaluation_result",
                    "component_name_version",
                ),
                "manual_concluded_comment",
            ),
            ("last_change", "last_change"),
        )
    )

    class Meta:
        model = License_Component
        fields = [
            "product",
            "branch",
            "effective_license_name",
            "effective_license_spdx_id",
            "effective_license_expression",
            "effective_non_spdx_license",
            "evaluation_result",
            "component_name_version",
            "component_purl_type",
            "origin_service",
            "manual_concluded_comment",
        ]


class LicenseComponentEvidenceFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(("name", "name"), ("license_component", "license_component"))
    )

    class Meta:
        model = License_Component_Evidence
        fields = ["name", "license_component"]


class LicenseFilter(FilterSet):
    spdx_id = CharFilter(field_name="spdx_id", lookup_expr="icontains")
    name = CharFilter(field_name="name", lookup_expr="icontains")
    exclude_license_group = NumberFilter(field_name="exclude_license_group", method="get_exclude_license_group")
    exclude_license_policy = NumberFilter(field_name="exclude_license_policy", method="get_exclude_license_policy")
    license_groups = ModelMultipleChoiceFilter(queryset=License.objects.none())

    def get_exclude_license_group(
        self, queryset: QuerySet, name: Any, value: Any  # pylint: disable=unused-argument
    ) -> QuerySet:
        if value is not None:
            return queryset.exclude(license_groups__id=value)
        return queryset

    def get_exclude_license_policy(
        self, queryset: QuerySet, name: Any, value: Any  # pylint: disable=unused-argument
    ) -> QuerySet:
        if value is not None:
            return queryset.exclude(license_policy_items__license_policy__id=value)
        return queryset

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("spdx_id", "spdx_id"),
            ("name", "name"),
            ("is_osi_approved", "is_osi_approved"),
            ("is_deprecated", "is_deprecated"),
        )
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.filters["license_groups"].queryset = get_license_groups()

    class Meta:
        model = License
        fields = ["spdx_id", "name", "is_osi_approved", "is_deprecated", "license_groups"]


class LicenseGroupFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    exclude_license_policy = NumberFilter(field_name="exclude_license_policy", method="get_exclude_license_policy")

    def get_exclude_license_policy(
        self, queryset: QuerySet, name: Any, value: Any  # pylint: disable=unused-argument
    ) -> QuerySet:
        if value is not None:
            return queryset.exclude(license_policy_items__license_policy__id=value)
        return queryset

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(("name", "name"), ("is_public", "is_public"))
    )

    class Meta:
        model = License_Group
        fields = ["name", "is_public", "licenses"]


class LicenseGroupMemberFilter(FilterSet):
    username = CharFilter(field_name="user__username", lookup_expr="icontains")
    full_name = CharFilter(field_name="user__full_name", lookup_expr="icontains")

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("user__full_name", "user_data.full_name"),
            ("license_group", "license_group"),
            ("user", "user"),
            ("is_manager", "is_manager"),
        )
    )

    class Meta:
        model = License_Group_Member
        fields = ["license_group", "user", "username", "full_name", "is_manager"]


class LicenseGroupAuthorizationGroupFilter(FilterSet):
    name = CharFilter(field_name="authorization_group__name", lookup_expr="icontains")

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("authorization_group__name", "authorization_group_data.name"),
            ("license_group", "license_group"),
            ("authorization_group", "authorization_group"),
            ("is_manager", "is_manager"),
        )
    )

    class Meta:
        model = License_Group_Authorization_Group_Member
        fields = ["license_group", "authorization_group", "name", "is_manager"]


class LicensePolicyFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    is_child = BooleanFilter(field_name="is_child", method="get_is_child")
    is_not_id = NumberFilter(field_name="is_not_id", method="get_is_not_id")
    license = NumberFilter(field_name="license", method="get_license_policies_with_license")
    license_group = NumberFilter(field_name="license_group", method="get_license_policies_with_license_group")

    def get_is_child(self, queryset: QuerySet, name: Any, value: Any) -> QuerySet:  # pylint: disable=unused-argument
        parent_null = not value
        return queryset.filter(parent__isnull=parent_null)

    def get_is_not_id(self, queryset: QuerySet, name: Any, value: Any) -> QuerySet:  # pylint: disable=unused-argument
        return queryset.exclude(pk=value)

    def get_license_policies_with_license(
        self, queryset: QuerySet, name: Any, value: Any  # pylint: disable=unused-argument
    ) -> QuerySet:
        return queryset.filter(license_policy_items__license=value)

    def get_license_policies_with_license_group(
        self, queryset: QuerySet, name: Any, value: Any  # pylint: disable=unused-argument
    ) -> QuerySet:
        return queryset.filter(license_policy_items__license_group=value)

    ordering = ExtendedOrderingFilter(
        # tuple-mapping retains order
        fields=(("name", "name"), (("parent__name", "name"), "parent_name"), ("is_public", "is_public"))
    )

    class Meta:
        model = License_Policy
        fields = ["name", "is_public", "parent"]


class LicensePolicyItemFilter(FilterSet):
    license_group_name = CharFilter(field_name="license_group__name", lookup_expr="icontains")
    license_spdx_id = CharFilter(field_name="license__spdx_id", lookup_expr="icontains")
    license_expression = CharFilter(field_name="license_expression", lookup_expr="icontains")
    non_spdx_license = CharFilter(field_name="non_spdx_license", lookup_expr="icontains")

    ordering = ExtendedOrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("license_policy__name", "license_policy_data.name"),
            (
                ("license_group__name", "license__spdx_id", "license_expression", "non_spdx_license"),
                "license_group",
            ),
            (("license__spdx_id", "license_group__name", "license_expression", "non_spdx_license"), "spdx_id"),
            (
                ("license_expression", "license_group__name", "license__spdx_id", "non_spdx_license"),
                "license_expression",
            ),
            (("non_spdx_license", "license_group__name", "license__spdx_id", "license_expression"), "non_spdx_license"),
            (
                (
                    "numerical_evaluation_result",
                    "license_group__name",
                    "license__spdx_id",
                    "license_expression",
                    "non_spdx_license",
                ),
                "evaluation_result",
            ),
        )
    )

    class Meta:
        model = License_Policy_Item
        fields = [
            "license_policy",
            "license_group_name",
            "license_spdx_id",
            "license_expression",
            "non_spdx_license",
            "evaluation_result",
            "license_group_name",
        ]


class LicensePolicyMemberFilter(FilterSet):
    username = CharFilter(field_name="user__username", lookup_expr="icontains")
    full_name = CharFilter(field_name="user__full_name", lookup_expr="icontains")

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("user__full_name", "user_data.full_name"),
            ("license_policy", "license_policy"),
            ("user", "user"),
            ("is_manager", "is_manager"),
        )
    )

    class Meta:
        model = License_Policy_Member
        fields = ["license_policy", "user", "username", "full_name", "is_manager"]


class LicensePolicyAuthorizationGroupFilter(FilterSet):
    name = CharFilter(field_name="authorization_group__name", lookup_expr="icontains")

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("authorization_group__name", "authorization_group_data.name"),
            ("license_policy", "license_policy"),
            ("authorization_group", "authorization_group"),
            ("is_manager", "is_manager"),
        )
    )

    class Meta:
        model = License_Policy_Authorization_Group_Member
        fields = ["license_policy", "authorization_group", "name", "is_manager"]
