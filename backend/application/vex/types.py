from dataclasses import dataclass
from typing import Optional


class VEX_Document_Type:
    VEX_DOCUMENT_TYPE_CSAF = "CSAF"
    VEX_DOCUMENT_TYPE_OPENVEX = "OpenVEX"
    VEX_DOCUMENT_TYPE_CYCLONEDX = "CycloneDX"

    VEX_DOCUMENT_TYPE_CHOICES = [
        (VEX_DOCUMENT_TYPE_CSAF, VEX_DOCUMENT_TYPE_CSAF),
        (VEX_DOCUMENT_TYPE_OPENVEX, VEX_DOCUMENT_TYPE_OPENVEX),
        (VEX_DOCUMENT_TYPE_CYCLONEDX, VEX_DOCUMENT_TYPE_CYCLONEDX),
    ]


class CSAF_Tracking_Status:
    CSAF_TRACKING_STATUS_DRAFT = "draft"
    CSAF_TRACKING_STATUS_FINAL = "final"
    CSAF_TRACKING_STATUS_INTERIM = "interim"

    CSAF_TRACKING_STATUS_CHOICES = [
        (CSAF_TRACKING_STATUS_DRAFT, CSAF_TRACKING_STATUS_DRAFT),
        (CSAF_TRACKING_STATUS_FINAL, CSAF_TRACKING_STATUS_FINAL),
        (CSAF_TRACKING_STATUS_INTERIM, CSAF_TRACKING_STATUS_INTERIM),
    ]


class CSAF_TLP_Label:
    CSAF_TLP_LABEL_AMBER = "AMBER"
    CSAF_TLP_LABEL_GREEN = "GREEN"
    CSAF_TLP_LABEL_RED = "RED"
    CSAF_TLP_LABEL_WHITE = "WHITE"

    CSAF_TLP_LABEL_CHOICES = [
        (CSAF_TLP_LABEL_AMBER, CSAF_TLP_LABEL_AMBER),
        (CSAF_TLP_LABEL_GREEN, CSAF_TLP_LABEL_GREEN),
        (CSAF_TLP_LABEL_RED, CSAF_TLP_LABEL_RED),
        (CSAF_TLP_LABEL_WHITE, CSAF_TLP_LABEL_WHITE),
    ]


class CSAF_Publisher_Category:
    CSAF_PUBLISHER_CATEGORY_COORDINATOR = "coordinator"
    CSAF_PUBLISHER_CATEGORY_DISCOVERER = "discoverer"
    CSAF_PUBLISHER_CATEGORY_OTHER = "other"
    CSAF_PUBLISHER_CATEGORY_TRANSLATOR = "translator"
    CSAF_PUBLISHER_CATEGORY_USER = "user"
    CSAF_PUBLISHER_CATEGORY_VENDOR = "vendor"

    CSAF_PUBLISHER_CATEGORY_CHOICES = [
        (CSAF_PUBLISHER_CATEGORY_COORDINATOR, CSAF_PUBLISHER_CATEGORY_COORDINATOR),
        (CSAF_PUBLISHER_CATEGORY_DISCOVERER, CSAF_PUBLISHER_CATEGORY_DISCOVERER),
        (CSAF_PUBLISHER_CATEGORY_OTHER, CSAF_PUBLISHER_CATEGORY_OTHER),
        (CSAF_PUBLISHER_CATEGORY_TRANSLATOR, CSAF_PUBLISHER_CATEGORY_TRANSLATOR),
        (CSAF_PUBLISHER_CATEGORY_USER, CSAF_PUBLISHER_CATEGORY_USER),
        (CSAF_PUBLISHER_CATEGORY_VENDOR, CSAF_PUBLISHER_CATEGORY_VENDOR),
    ]


class CSAF_Status:
    CSAF_STATUS_NOT_AFFECTED = "known_not_affected"
    CSAF_STATUS_AFFECTED = "known_affected"
    CSAF_STATUS_FIXED = "fixed"
    CSAF_STATUS_UNDER_INVESTIGATION = "under_investigation"


class CSAF_Branch_Category:
    CSAF_BRANCH_CATEGORY_ARCHITECTURE = "architecture"
    CSAF_BRANCH_CATEGORY_HOST_NAME = "host_name"
    CSAF_BRANCH_CATEGORY_LANGUAGE = "language"
    CSAF_BRANCH_CATEGORY_LEGACY = "legacy"
    CSAF_BRANCH_CATEGORY_PATCH_LEVEL = "patch_level"
    CSAF_BRANCH_CATEGORY_PRODUCT_FAMILY = "product_family"
    CSAF_BRANCH_CATEGORY_PRODUCT_NAME = "product_name"
    CSAF_BRANCH_CATEGORY_PRODUCT_VERSION = "product_version"
    CSAF_BRANCH_CATEGORY_PRODUCT_VERSION_RANGE = "product_version_range"
    CSAF_BRANCH_CATEGORY_SERVICE_PACK = "service_pack"
    CSAF_BRANCH_CATEGORY_SPECIFICATION = "specification"
    CSAF_BRANCH_CATEGORY_VENDOR = "vendor"


class CSAF_Relationship_Category:
    CSAF_RELATIONSHIP_CATEGORY_DEFAULT_COMPONENT = "default_component_of"
    CSAF_RELATIONSHIP_CATEGORY_EXTERNAL_COMPONENT = "external_component_of"
    CSAF_RELATIONSHIP_CATEGORY_INSTALLED_ON = "installed_on"
    CSAF_RELATIONSHIP_CATEGORY_INSTALLED_WITH = "installed_with"
    CSAF_RELATIONSHIP_CATEGORY_OPTIONAL_COMPONENT = "optional_component_of"


@dataclass(frozen=True)
class CSAFProductIdentificationHelper:
    cpe: Optional[str]
    purl: Optional[str]


@dataclass(frozen=True)
class CSAFFullProductName:
    name: str
    product_id: str
    product_identification_helper: Optional[CSAFProductIdentificationHelper] = None


@dataclass()
class CSAFProductBranch:
    name: str
    category: str
    product: Optional[CSAFFullProductName] = None
    branches: Optional[list["CSAFProductBranch"]] = None


@dataclass()
class CSAFProductRelationship:
    category: str
    product_reference: str
    relates_to_product_reference: str
    full_product_name: CSAFFullProductName


@dataclass()
class CSAFProductTree:
    branches: list[CSAFProductBranch]
    relationships: list[CSAFProductRelationship]


@dataclass(frozen=True)
class CSAFNote:
    category: str
    text: str
    title: Optional[str] = None


@dataclass(frozen=True)
class CSAFFlag:
    label: str
    product_ids: list[str]


@dataclass(frozen=True)
class CSAFId:
    system_name: str
    text: str


@dataclass()
class CSAFProductStatus:
    fixed: list[str]
    known_affected: list[str]
    known_not_affected: list[str]
    under_investigation: list[str]


@dataclass()
class CSAFReference:
    category: str
    url: str
    summary: str


@dataclass()
class CSAFRemediation:
    category: str
    details: str
    product_ids: list[str]


@dataclass()
class CSAFThreat:
    category: str
    details: str
    product_ids: list[str]


@dataclass()
class CSAFVulnerability:
    cve: Optional[str]
    title: Optional[str]
    notes: list[CSAFNote]
    flags: list[CSAFFlag]
    ids: list[CSAFId]
    product_status: CSAFProductStatus
    references: list[CSAFReference]
    remediations: list[CSAFRemediation]
    threats: list[CSAFThreat]


@dataclass()
class CSAFPublisher:
    name: str
    category: str
    namespace: str


@dataclass()
class CSAFEngine:
    name: str
    version: str


@dataclass()
class CSAFGenerator:
    engine: CSAFEngine


@dataclass(frozen=True)
class CSAFRevisionHistory:
    date: str
    number: str
    summary: str


@dataclass()
class CSAFTracking:
    id: str
    initial_release_date: str
    current_release_date: str
    version: str
    status: str
    generator: CSAFGenerator
    revision_history: list[CSAFRevisionHistory]


@dataclass()
class CSAFTLP:
    label: str


@dataclass()
class CSAFDistribution:
    tlp: CSAFTLP


@dataclass()
class CSAFDocument:
    category: str
    csaf_version: str
    title: str
    publisher: CSAFPublisher
    tracking: CSAFTracking
    distribution: CSAFDistribution


@dataclass()
class CSAFRoot:
    document: CSAFDocument
    product_tree: Optional[CSAFProductTree]
    vulnerabilities: list[CSAFVulnerability]


class OpenVEX_Status:
    OPENVEX_STATUS_NOT_AFFECTED = "not_affected"
    OPENVEX_STATUS_AFFECTED = "affected"
    OPENVEX_STATUS_FIXED = "fixed"
    OPENVEX_STATUS_UNDER_INVESTIGATION = "under_investigation"


class CycloneDX_Analysis_State:
    CYCLONEDX_STATE_RESOLVED = "resolved"
    CYCLONEDX_STATE_RESOLVED_WITH_PEDIGREE = "resolved_with_pedigree"
    CYCLONEDX_STATE_EXPLOITABLE = "exploitable"
    CYCLONEDX_STATE_IN_TRIAGE = "in_triage"
    CYCLONEDX_STATE_FALSE_POSITIVE = "false_positive"
    CYCLONEDX_STATE_NOT_AFFECTED = "not_affected"


class CycloneDX_Analysis_Justification:
    CYCLONEDX_JUSTIFICATION_CODE_NOT_PRESENT = "code_not_present"
    CYCLONEDX_JUSTIFICATION_CODE_NOT_REACHABLE = "code_not_reachable"
    CYCLONEDX_JUSTIFICATION_REQUIRES_CONFIGURATION = "requires_configuration"
    CYCLONEDX_JUSTIFICATION_REQUIRES_DEPENDENCY = "requires_dependency"
    CYCLONEDX_JUSTIFICATION_REQUIRES_ENVIRONMENT = "requires_environment"
    CYCLONEDX_JUSTIFICATION_PROTECTED_BY_COMPILER = "protected_by_compiler"
    CYCLONEDX_JUSTIFICATION_PROTECTED_AT_RUNTIME = "protected_at_runtime"
    CYCLONEDX_JUSTIFICATION_PROTECTED_AT_PERIMETER = "protected_at_perimeter"
    CYCLONEDX_JUSTIFICATION_PROTECTED_BY_MITIGATING_CONTROL = "protected_by_mitigating_control"


@dataclass(frozen=True)
class OpenVEXSubcomponent:
    id: str


@dataclass(frozen=True)
class OpenVEXProductIdentifiers:
    cpe23: Optional[str]
    purl: Optional[str]


@dataclass(frozen=True)
class OpenVEXProduct:
    id: str
    identifiers: Optional[OpenVEXProductIdentifiers]
    subcomponents: list[OpenVEXSubcomponent]


@dataclass()
class OpenVEXVulnerability:
    id: Optional[str]
    name: str
    description: Optional[str] = None


@dataclass
class OpenVEXStatement:
    status: str
    status_notes: Optional[str]
    justification: Optional[str]
    action_statement: Optional[str]
    impact_statement: Optional[str]
    vulnerability: Optional[OpenVEXVulnerability]
    products: list[OpenVEXProduct]


@dataclass
class OpenVEXDocument:
    context: str
    id: str
    version: int
    author: str
    role: str
    timestamp: str
    last_updated: str
    tooling: str
    statements: list[OpenVEXStatement]

    def get_base_id(self) -> str:
        if len(self.id) > 36:
            return self.id[-36:]
        return ""


class VEX_Status:
    VEX_STATUS_NOT_AFFECTED = "not_affected"
    VEX_STATUS_AFFECTED = "affected"
    VEX_STATUS_FIXED = "fixed"
    VEX_STATUS_UNDER_INVESTIGATION = "under_investigation"
    VEX_STATUS_FALSE_POSITIVE = "false_positive"

    VEX_STATUS_LIST = [
        VEX_STATUS_NOT_AFFECTED,
        VEX_STATUS_AFFECTED,
        VEX_STATUS_FIXED,
        VEX_STATUS_UNDER_INVESTIGATION,
        VEX_STATUS_FALSE_POSITIVE,
    ]

    VEX_STATUS_CHOICES = [
        (VEX_STATUS_NOT_AFFECTED, VEX_STATUS_NOT_AFFECTED),
        (VEX_STATUS_AFFECTED, VEX_STATUS_AFFECTED),
        (VEX_STATUS_FIXED, VEX_STATUS_FIXED),
        (VEX_STATUS_UNDER_INVESTIGATION, VEX_STATUS_UNDER_INVESTIGATION),
        (VEX_STATUS_FALSE_POSITIVE, VEX_STATUS_FALSE_POSITIVE),
    ]
