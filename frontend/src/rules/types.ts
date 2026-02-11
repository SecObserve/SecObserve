import { Identifier, RaRecord } from "react-admin";

export interface GeneralRule extends RaRecord {
    id: Identifier;
    name: string;
    description: string;
    parser: Identifier;
    scanner_prefix: string;
    title: string;
    description_observation: string;
    origin_component_name_version: string;
    origin_component_purl: string;
    origin_docker_image_name_tag: string;
    origin_endpoint_url: string;
    origin_service_name: string;
    origin_source_file: string;
    origin_cloud_qualified_resource: string;
    new_severity: string;
    new_status: string;
}

export interface ProductRule extends RaRecord {
    id: Identifier;
    name: string;
    description: string;
    product: Identifier;
    parser: Identifier;
    scanner_prefix: string;
    title: string;
    origin_component_name_version: string;
    origin_component_purl: string;
    origin_docker_image_name_tag: string;
    origin_endpoint_url: string;
    origin_service_name: string;
    origin_source_file: string;
    origin_cloud_qualified_resource: string;
    new_severity: string;
    new_status: string;
    enabled: boolean;
}

export const RULE_STATUS_APPROVED = "Approved";
export const RULE_STATUS_NEEDS_APPROVAL = "Needs approval";
export const RULE_STATUS_REJECTED = "Rejected";
export const RULE_STATUS_AUTO_APPROVED = "Auto approved";

export const RULE_STATUS_CHOICES = [
    { id: RULE_STATUS_APPROVED, name: RULE_STATUS_APPROVED },
    { id: RULE_STATUS_REJECTED, name: RULE_STATUS_REJECTED },
    { id: RULE_STATUS_NEEDS_APPROVAL, name: RULE_STATUS_NEEDS_APPROVAL },
    { id: RULE_STATUS_AUTO_APPROVED, name: RULE_STATUS_AUTO_APPROVED },
];

export const RULE_STATUS_CHOICES_APPROVAL = [
    { id: RULE_STATUS_APPROVED, name: RULE_STATUS_APPROVED },
    { id: RULE_STATUS_REJECTED, name: RULE_STATUS_REJECTED },
];

export const RULE_TYPE_FIELDS = "Fields";
export const RULE_TYPE_REGO = "Rego";

export const RULE_TYPE_CHOICES = [
    { id: RULE_TYPE_FIELDS, name: RULE_TYPE_FIELDS },
    { id: RULE_TYPE_REGO, name: RULE_TYPE_REGO },
];
