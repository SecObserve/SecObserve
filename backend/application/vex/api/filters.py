from django_filters import CharFilter, FilterSet, OrderingFilter

from application.vex.models import (
    CSAF,
    CSAF_Branch,
    CSAF_Vulnerability,
    CycloneDX,
    CycloneDX_Branch,
    CycloneDX_Vulnerability,
    OpenVEX,
    OpenVEX_Branch,
    OpenVEX_Vulnerability,
    VEX_Counter,
    VEX_Document,
    VEX_Statement,
)


class CSAFFilter(FilterSet):
    vulnerability_names__name = CharFilter(
        field_name="vulnerability_names__name", lookup_expr="icontains", distinct=True
    )
    branches__branch__name = CharFilter(field_name="branches__branch__name", lookup_expr="icontains", distinct=True)

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("user__full_name", "user_full_name"),
            ("product__name", "product_data.name"),
            ("document_id_prefix", "document_id_prefix"),
            ("document_base_id", "document_base_id"),
            ("version", "version"),
            ("content_hash", "content_hash"),
            ("title", "title"),
            ("tlp_label", "tlp_label"),
            ("tracking_initial_release_date", "tracking_initial_release_date"),
            ("tracking_current_release_date", "tracking_current_release_date"),
            ("tracking_status", "tracking_status"),
            ("publisher_name", "publisher_name"),
            ("publisher_category", "publisher_category"),
            ("publisher_namespace", "publisher_namespace"),
        ),
    )

    class Meta:
        model = CSAF
        fields = [
            "product",
            "vulnerability_names__name",
            "branches__branch__name",
            "document_id_prefix",
            "title",
            "publisher_name",
        ]


class CSAFVulnerabilityFilter(FilterSet):
    class Meta:
        model = CSAF_Vulnerability
        fields = [
            "csaf",
            "name",
        ]


class CSAFBranchFilter(FilterSet):
    class Meta:
        model = CSAF_Branch
        fields = [
            "csaf",
            "branch__name",
        ]


class OpenVEXFilter(FilterSet):
    vulnerability_names__name = CharFilter(
        field_name="vulnerability_names__name", lookup_expr="icontains", distinct=True
    )
    branches__branch__name = CharFilter(field_name="branches__branch__name", lookup_expr="icontains", distinct=True)

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("user__full_name", "user_full_name"),
            ("product__name", "product_data.name"),
            ("document_id_prefix", "document_id_prefix"),
            ("document_base_id", "document_base_id"),
            ("version", "version"),
            ("content_hash", "content_hash"),
            ("author", "author"),
            ("role", "role"),
            ("timestamp", "timestamp"),
            ("last_updated", "last_updated"),
        ),
    )

    class Meta:
        model = OpenVEX
        fields = [
            "product",
            "vulnerability_names__name",
            "branches__branch__name",
            "document_id_prefix",
            "author",
        ]


class OpenVEXVulnerabilityFilter(FilterSet):
    class Meta:
        model = OpenVEX_Vulnerability
        fields = [
            "openvex",
            "name",
        ]


class OpenVEXBranchFilter(FilterSet):
    class Meta:
        model = OpenVEX_Branch
        fields = [
            "openvex",
            "branch__name",
        ]


class CycloneDXFilter(FilterSet):
    vulnerability_names__name = CharFilter(
        field_name="vulnerability_names__name", lookup_expr="icontains", distinct=True
    )
    branches__branch__name = CharFilter(field_name="branches__branch__name", lookup_expr="icontains", distinct=True)

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("user__full_name", "user_full_name"),
            ("product__name", "product_data.name"),
            ("document_base_id", "document_base_id"),
            ("document_id_prefix", "document_id_prefix"),
            ("version", "version"),
            ("content_hash", "content_hash"),
            ("author", "author"),
            ("manufacturer", "manufacturer"),
            ("first_issued", "first_issued"),
            ("last_updated", "last_updated"),
        ),
    )

    class Meta:
        model = CycloneDX
        fields = [
            "product",
            "vulnerability_names__name",
            "branches__branch__name",
            "document_id_prefix",
            "author",
        ]


class CycloneDXVulnerabilityFilter(FilterSet):
    class Meta:
        model = CycloneDX_Vulnerability
        fields = [
            "cyclonedx",
            "name",
        ]


class CycloneDXBranchFilter(FilterSet):
    class Meta:
        model = CycloneDX_Branch
        fields = [
            "cyclonedx",
            "branch__name",
        ]


class VEXCounterFilter(FilterSet):
    document_id_prefix = CharFilter(field_name="document_id_prefix", lookup_expr="icontains", distinct=True)

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("document_id_prefix", "document_id_prefix"),
            ("year", "year"),
        ),
    )

    class Meta:
        model = VEX_Counter
        fields = [
            "document_id_prefix",
            "year",
        ]


class VEXDocumentFilter(FilterSet):
    document_id = CharFilter(field_name="document_id", lookup_expr="icontains", distinct=True)
    author = CharFilter(field_name="author", lookup_expr="icontains", distinct=True)
    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("type", "type"),
            ("document_id", "document_id"),
            ("version", "version"),
            ("current_release_date", "current_release_date"),
            ("initial_release_date", "initial_release_date"),
            ("author", "author"),
            ("role", "role"),
        )
    )

    class Meta:
        model = VEX_Document
        fields = "__all__"


class VEXStatementFilter(FilterSet):
    vulnerability_id = CharFilter(field_name="vulnerability_id", lookup_expr="icontains", distinct=True)

    ordering = OrderingFilter(
        # tuple-mapping retains order
        fields=(
            ("vulnerability_id", "vulnerability_id"),
            ("status", "status"),
            ("justification", "justification"),
            ("impact", "impact"),
            ("remediation", "remediation"),
            ("product_purl", "product_purl"),
            ("component_cyclonedx_bom_link", "component_cyclonedx_bom_link"),
        )
    )

    class Meta:
        model = VEX_Statement
        fields = "__all__"
