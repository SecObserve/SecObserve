import { FC } from "react";
import { BooleanInput, SelectArrayInput, SelectInput, TextArrayField, useRecordContext } from "react-admin";

import { PERMISSION_WEBHOOK_DELETE, PERMISSION_WEBHOOK_EDIT } from "../../access_control/types";
import { validate_required, validate_required_255, validate_required_2048 } from "../../commons/custom_validators";
import { is_superuser } from "../../commons/functions";
import { TextInputWide } from "../../commons/layout/themes";
import { OBSERVATION_SEVERITY_CHOICES } from "../../core/types";
import { WEBHOOK_EVENT_TYPE_CHOICES, Webhook } from "../types";

// Global webhooks (no product) are superuser-only, like in the backend
export const canEditWebhook = (webhook: Webhook | undefined) =>
    webhook?.product ? !!webhook.product_data?.permissions?.includes(PERMISSION_WEBHOOK_EDIT) : is_superuser();

export const canDeleteWebhook = (webhook: Webhook | undefined) =>
    webhook?.product ? !!webhook.product_data?.permissions?.includes(PERMISSION_WEBHOOK_DELETE) : is_superuser();

const get_event_type_name = (event_type: string) =>
    WEBHOOK_EVENT_TYPE_CHOICES.find((choice) => choice.id === event_type)?.name ?? event_type;

// label is read by Datagrid and Labeled
export const WebhookEventTypesField: FC<{ label?: string }> = () => {
    const webhook = useRecordContext<Webhook>();
    if (!webhook) return null;
    return (
        <TextArrayField
            source="event_types"
            record={{ ...webhook, event_types: webhook.event_types.map(get_event_type_name) }}
        />
    );
};

export const WebhookFields = () => (
    <>
        <TextInputWide autoFocus source="name" validate={validate_required_255} />
        <TextInputWide source="url" label="URL" validate={validate_required_2048} />
        <SelectArrayInput
            source="event_types"
            choices={WEBHOOK_EVENT_TYPE_CHOICES}
            validate={validate_required}
            sx={{ width: "30em" }}
        />
        <SelectInput
            source="min_severity"
            label="Minimum severity"
            choices={OBSERVATION_SEVERITY_CHOICES}
            emptyText="All severities"
            emptyValue=""
            helperText="Applies to observation and assessment events"
            sx={{ width: "30em" }}
        />
        <BooleanInput source="active" defaultValue={true} />
    </>
);
