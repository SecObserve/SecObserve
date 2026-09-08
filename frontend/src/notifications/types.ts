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
    product_rule_to_be_reviewed: boolean;
}

export interface ProductNotificationPair {
    // null while the user does not override the settings the product inherits
    product_notification: ProductNotification | null;
    // null for a product group, its settings are not an override
    template_notification: ProductNotification | null;
}
