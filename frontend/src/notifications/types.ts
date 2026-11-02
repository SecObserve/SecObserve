import { Identifier, RaRecord } from "react-admin";

export const TYPE_CHOICES = [
    { id: "Exception", name: "Exception" },
    { id: "Observation", name: "Observation" },
    { id: "Observation title", name: "Observation title" },
    { id: "Security gate", name: "Security gate" },
    { id: "Task", name: "Task" },
];

export interface Notification extends RaRecord {
    id: Identifier;
    type: string;
    name: string;
    created: Date;
    message: string;
    user: Identifier;
    observation: Identifier;
    function: string;
    arguments: string;
}

export interface ProductNotification extends RaRecord {
    id: Identifier;
    product: Identifier | null;
    product_name: string | null;
    user: Identifier;
    user_full_name: string | null;
    security_gate_changed: boolean;
    observation_new_changed: boolean;
    observation_to_be_reviewed: boolean;
    assessment_to_be_reviewed: boolean;
    assessment_approval_receipt: boolean;
    product_rule_to_be_reviewed: boolean;
    product_rule_approval_receipt: boolean;
}

export type NotificationSettingSource =
    | "security_gate_changed"
    | "observation_new_changed"
    | "observation_to_be_reviewed"
    | "assessment_to_be_reviewed"
    | "assessment_approval_receipt"
    | "product_rule_to_be_reviewed"
    | "product_rule_approval_receipt";

export type NotificationSetting = {
    source: NotificationSettingSource;
    label: string;
};

export const NOTIFICATION_SETTINGS: NotificationSetting[] = [
    { source: "security_gate_changed", label: "Security gate changed" },
    { source: "observation_new_changed", label: "Observation new or changed" },
    { source: "observation_to_be_reviewed", label: "Observation to be reviewed" },
    { source: "assessment_to_be_reviewed", label: "Assessment to be reviewed" },
    { source: "assessment_approval_receipt", label: "Assessment approval receipt" },
    { source: "product_rule_to_be_reviewed", label: "Product rule to be reviewed" },
    { source: "product_rule_approval_receipt", label: "Product rule approval receipt" },
];

export interface ProductNotificationPair {
    // null while the user does not override the settings the product inherits
    product_notification: ProductNotification | null;
    // null for a product group, its settings are not an override
    template_notification: ProductNotification | null;
}

export const WEBHOOK_EVENT_TYPE_CHOICES = [
    { id: "observation.created", name: "Observation created" },
    { id: "observation.review_requested", name: "Observation review requested" },
    { id: "assessment.approval_requested", name: "Assessment approval requested" },
    { id: "assessment.approval_decided", name: "Assessment approval decided" },
    { id: "rule.approval_requested", name: "Rule approval requested" },
    { id: "rule.approval_decided", name: "Rule approval decided" },
    { id: "import.completed", name: "Import completed" },
    { id: "security_gate.changed", name: "Security gate changed" },
];

export interface Webhook extends RaRecord {
    id: Identifier;
    product: Identifier | null;
    product_data: { name: string; permissions: number[] } | null;
    name: string;
    url: string;
    event_types: string[];
    min_severity: string;
    active: boolean;
    consecutive_failures: number;
    next_attempt_at: string | null;
    created: string;
}

export interface WebhookDelivery extends RaRecord {
    id: Identifier;
    webhook: Identifier;
    event_id: string;
    event_type: string;
    payload: string;
    status: "Pending" | "Succeeded" | "Failed";
    attempts: number;
    created: string;
    last_attempt_at: string | null;
    response_status_code: number | null;
    error: string;
}
