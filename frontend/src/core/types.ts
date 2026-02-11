import { Identifier, RaRecord } from "react-admin";

import { Parser } from "../import_observations/types";

export interface Product extends RaRecord {
    id: Identifier;
    name: string;
    description: string;
    repository_prefix: string;
    repository_default_branch: Identifier;
    repository_branch_housekeeping_active: boolean;
    repository_branch_housekeeping_keep_inactive_days: number;
    repository_branch_housekeeping_exempt_branches: string;
    security_gate_passed: boolean;
    security_gate_active: boolean | null;
    security_gate_threshold_critical: number;
    security_gate_threshold_high: number;
    security_gate_threshold_medium: number;
    security_gate_threshold_low: number;
    security_gate_threshold_none: number;
    security_gate_threshold_unknown: number;
    apply_general_rules: boolean;
    notification_ms_teams_webhook: string;
    notification_slack_webhook: string;
    notification_email_to: string;
    issue_tracker_active: boolean;
    issue_tracker_type: string;
    issue_tracker_base_url: string;
    issue_tracker_username: string;
    issue_tracker_api_key: string;
    issue_tracker_project_id: string;
    issue_tracker_labels: string;
    issue_tracker_issue_type: string;
    issue_tracker_status_closed: string;
    issue_tracker_minimum_severity: string;
    last_observation_change: string;
}

export const ISSUE_TRACKER_TYPE_CHOICES = [
    { id: "GitHub", name: "GitHub" },
    { id: "GitLab", name: "GitLab" },
    { id: "Jira", name: "Jira" },
];

export interface ProductGroup extends RaRecord {
    id: Identifier;
    name: string;
    description: string;
    repository_branch_housekeeping_active: boolean;
    repository_branch_housekeeping_keep_inactive_days: number;
    repository_branch_housekeeping_exempt_branches: string;
    notification_ms_teams_webhook: string;
    notification_slack_webhook: string;
    notification_email_to: string;
}

export interface Observation extends RaRecord {
    id: Identifier;
    product: Product;
    branch: Identifier;
    parser: Parser;
    title: string;
    description: string;
    recommendation: string;
    current_severity: string;
    parser_severity: string;
    assessment_severity: string;
    rule_rego_severity: string;
    rule_severity: string;
    current_status: string;
    parser_status: string;
    assessment_status: string;
    rule_rego_status: string;
    rule_status: string;
    scanner_observation_id: string;
    origin_component_name: string;
    origin_component_version: string;
    origin_component_name_version: string;
    origin_component_purl: string;
    origin_component_cpe: string;
    origin_docker_image_name: string;
    origin_docker_image_tag: string;
    origin_docker_image_name_tag: string;
    origin_docker_image_name_tag_short: string;
    origin_docker_image_digest: string;
    origin_endpoint_url: string;
    origin_endpoint_scheme: string;
    origin_endpoint_hostname: string;
    origin_endpoint_port: number;
    origin_endpoint_path: string;
    origin_endpoint_params: string;
    origin_endpoint_query: string;
    origin_endpoint_fragment: string;
    origin_service_name: string;
    origin_source_file: string;
    origin_source_file_url: string;
    origin_source_line_start: number;
    origin_source_line_end: number;
    origin_cloud_provider: string;
    origin_cloud_account_subscription_project: string;
    origin_cloud_resource: string;
    origin_cloud_resource_type: string;
    origin_cloud_qualified_resource: string;
    cvss3_score: number;
    cvss3_vector: string;
    cvss4_score: number;
    cvss4_vector: string;
    epss_score: number;
    epss_percentile: number;
    cwe: number;
    found: Date;
    scanner: string;
    upload_filename: string;
    api_configuration_name: string;
    import_last_seen: Date;
    created: Date;
    modified: Date;
    general_rule: Identifier;
    product_rule: Identifier;
    issue_tracker_issue_id: string;
    issue_tracker_issue_url: string;
    has_potential_duplicates: boolean;
    current_vex_justification: string;
    parser_vex_justification: string;
    assessment_vex_justification: string;
    rule_vex_justification: string;
    origin_component_purl_type: string;
}

export const OBSERVATION_SEVERITY_CRITICAL = "Critical";
export const OBSERVATION_SEVERITY_HIGH = "High";
export const OBSERVATION_SEVERITY_MEDIUM = "Medium";
export const OBSERVATION_SEVERITY_LOW = "Low";
export const OBSERVATION_SEVERITY_NONE = "None";
export const OBSERVATION_SEVERITY_UNKNOWN = "Unknown";

export const OBSERVATION_SEVERITY_CHOICES = [
    { id: OBSERVATION_SEVERITY_CRITICAL, name: OBSERVATION_SEVERITY_CRITICAL },
    { id: OBSERVATION_SEVERITY_HIGH, name: OBSERVATION_SEVERITY_HIGH },
    { id: OBSERVATION_SEVERITY_MEDIUM, name: OBSERVATION_SEVERITY_MEDIUM },
    { id: OBSERVATION_SEVERITY_LOW, name: OBSERVATION_SEVERITY_LOW },
    { id: OBSERVATION_SEVERITY_NONE, name: OBSERVATION_SEVERITY_NONE },
    { id: OBSERVATION_SEVERITY_UNKNOWN, name: OBSERVATION_SEVERITY_UNKNOWN },
];

export const OBSERVATION_STATUS_OPEN = "Open";
export const OBSERVATION_STATUS_RESOLVED = "Resolved";
export const OBSERVATION_STATUS_DUPLICATE = "Duplicate";
export const OBSERVATION_STATUS_FALSE_POSITIVE = "False positive";
export const OBSERVATION_STATUS_IN_REVIEW = "In review";
export const OBSERVATION_STATUS_NOT_AFFECTED = "Not affected";
export const OBSERVATION_STATUS_NOT_SECURITY = "Not security";
export const OBSERVATION_STATUS_RISK_ACCEPTED = "Risk accepted";

export const OBSERVATION_STATUS_CHOICES = [
    { id: OBSERVATION_STATUS_OPEN, name: OBSERVATION_STATUS_OPEN },
    { id: OBSERVATION_STATUS_RESOLVED, name: OBSERVATION_STATUS_RESOLVED },
    { id: OBSERVATION_STATUS_DUPLICATE, name: OBSERVATION_STATUS_DUPLICATE },
    {
        id: OBSERVATION_STATUS_FALSE_POSITIVE,
        name: OBSERVATION_STATUS_FALSE_POSITIVE,
    },
    { id: OBSERVATION_STATUS_IN_REVIEW, name: OBSERVATION_STATUS_IN_REVIEW },
    {
        id: OBSERVATION_STATUS_NOT_AFFECTED,
        name: OBSERVATION_STATUS_NOT_AFFECTED,
    },
    {
        id: OBSERVATION_STATUS_NOT_SECURITY,
        name: OBSERVATION_STATUS_NOT_SECURITY,
    },
    {
        id: OBSERVATION_STATUS_RISK_ACCEPTED,
        name: OBSERVATION_STATUS_RISK_ACCEPTED,
    },
];

export const AGE_CHOICES = [
    { id: "Today", name: "Today" },
    { id: "Past 7 days", name: "Past 7 days" },
    { id: "Past 30 days", name: "Past 30 days" },
    { id: "Past 90 days", name: "Past 90 days" },
    { id: "Past 365 days", name: "Past 365 days" },
];

export const OBSERVATION_VEX_JUSTIFICATION_COMPONENT_NOT_PRESENT = "component_not_present";
export const OBSERVATION_VEX_JUSTIFICATION_VULNERABLE_CODE_NOT_PRESENT = "vulnerable_code_not_present";
export const OBSERVATION_VEX_JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY =
    "vulnerable_code_cannot_be_controlled_by_adversary";
export const OBSERVATION_VEX_JUSTIFICATION_VULNERABLE_CODE_NOT_IN_EXECUTE_PATH = "vulnerable_code_not_in_execute_path";
export const OBSERVATION_VEX_JUSTIFICATION_INLINE_MITIGATIONS_ALREADY_EXIST = "inline_mitigations_already_exist";

export const OBSERVATION_VEX_JUSTIFICATION_CHOICES = [
    {
        id: OBSERVATION_VEX_JUSTIFICATION_COMPONENT_NOT_PRESENT,
        name: "Component not present",
    },
    {
        id: OBSERVATION_VEX_JUSTIFICATION_VULNERABLE_CODE_NOT_PRESENT,
        name: "Vulnerable code not present",
    },
    {
        id: OBSERVATION_VEX_JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY,
        name: "Vulnerable code cannot be controlled by adversary",
    },
    {
        id: OBSERVATION_VEX_JUSTIFICATION_VULNERABLE_CODE_NOT_IN_EXECUTE_PATH,
        name: "Vulnerable code not in execute path",
    },
    {
        id: OBSERVATION_VEX_JUSTIFICATION_INLINE_MITIGATIONS_ALREADY_EXIST,
        name: "Inline mitigations already exist",
    },
];

export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_CODE_NOT_PRESENT = "code_not_present";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_CODE_NOT_REACHABLE = "code_not_reachable";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION = "requires_configuration";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_REQUIRES_DEPENDENCY = "requires_dependency";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_REQUIRES_ENVIRONMENT = "requires_environment";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_BY_COMPILER = "protected_by_compiler";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_AT_RUNTIME = "protected_at_runtime";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_AT_PERIMETER = "protected_at_perimeter";
export const OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_BY_MITIGATING_CONTROL =
    "protected_by_mitigating_control";

export const OBSERVATION_CYCLONEDX_VEX_JUSTIFICATION_CHOICES = [
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_CODE_NOT_PRESENT,
        name: "Code not present",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_CODE_NOT_REACHABLE,
        name: "Code not reachable",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION,
        name: "Requires configuration",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_REQUIRES_DEPENDENCY,
        name: "Requires dependency",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_REQUIRES_ENVIRONMENT,
        name: "Requires environment",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_BY_COMPILER,
        name: "Protected by compiler",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_AT_RUNTIME,
        name: "Protected at runtime",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_AT_PERIMETER,
        name: "Protected at perimeter",
    },
    {
        id: OBSERVATION_VEX_CYCLONEDX_JUSTIFICATION_CYCLONEDX_PROTECTED_BY_MITIGATING_CONTROL,
        name: "Protected by mitigation control",
    },
];

export const ASSESSMENT_STATUS_APPROVED = "Approved";
export const ASSESSMENT_STATUS_NEEDS_APPROVAL = "Needs approval";
export const ASSESSMENT_STATUS_REJECTED = "Rejected";

export const ASSESSMENT_STATUS_CHOICES = [
    { id: ASSESSMENT_STATUS_APPROVED, name: ASSESSMENT_STATUS_APPROVED },
    { id: ASSESSMENT_STATUS_REJECTED, name: ASSESSMENT_STATUS_REJECTED },
];

export const PURL_TYPE_CHOICES = [
    { id: "alpm", name: "alpm" },
    { id: "apk", name: "APK" },
    { id: "bitbucket", name: "Bitbucket" },
    { id: "bitnami", name: "Bitnami" },
    { id: "cargo", name: "Rust" },
    { id: "cocoapods", name: "Cocoapods" },
    { id: "composer", name: "Composer" },
    { id: "conan", name: "Conan" },
    { id: "conda", name: "Conda" },
    { id: "cpan", name: "CPAN Perl" },
    { id: "cran", name: "CRAN R" },
    { id: "deb", name: "Debian" },
    { id: "docker", name: "Docker" },
    { id: "gem", name: "Ruby Gem" },
    { id: "generic", name: "Generic" },
    { id: "github", name: "GitHub" },
    { id: "golang", name: "Go" },
    { id: "hackage", name: "Hackage" },
    { id: "hex", name: "Hex" },
    { id: "huggingface", name: "Huggingface" },
    { id: "luarocks", name: "Lua" },
    { id: "maven", name: "Maven" },
    { id: "mlflow", name: "MLflow" },
    { id: "npm", name: "NPM" },
    { id: "nuget", name: "NuGet" },
    { id: "oci", name: "OCI" },
    { id: "pub", name: "Dart" },
    { id: "pypi", name: "PyPI" },
    { id: "rpm", name: "RPM" },
    { id: "qpkg", name: "QNX" },
    { id: "swid", name: "SWID" },
    { id: "swift", name: "Swift" },
];
