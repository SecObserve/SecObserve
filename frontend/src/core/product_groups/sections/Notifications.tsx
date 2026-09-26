import { Stack } from "@mui/material";
import { AutocompleteArrayInput, Labeled, NumberInput, TextArrayField, TextField, useRecordContext } from "react-admin";

import WebhookTestButton from "../../../commons/custom_fields/WebhookTestButton";
import { validate_255, validate_2048 } from "../../../commons/custom_validators";
import { feature_email } from "../../../commons/functions";
import { AutocompleteInputMedium, TextInputExtraWide } from "../../../commons/layout/themes";
import { OBSERVATION_SEVERITY_CHOICES, OBSERVATION_STATUS_CHOICES } from "../../types";

export const NotificationsInputs = () => (
    <Stack spacing={1}>
        {feature_email() && (
            <TextInputExtraWide
                source="notification_email_to"
                label="Comma separated email to addresses to send notifications via email"
                validate={validate_255}
            />
        )}
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <TextInputExtraWide
                source="notification_ms_teams_webhook"
                label="Webhook URL to send notifications to MS Teams"
                validate={validate_2048}
            />
            <WebhookTestButton webhookSource="notification_ms_teams_webhook" webhookType="msteams" />
        </Stack>
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <TextInputExtraWide
                source="notification_slack_webhook"
                label="Webhook URL to send notifications to Slack"
                validate={validate_2048}
            />
            <WebhookTestButton webhookSource="notification_slack_webhook" webhookType="slack" />
        </Stack>
        <AutocompleteInputMedium
            source="observation_notification_min_severity"
            label="Minimum severity for observation notifications"
            choices={OBSERVATION_SEVERITY_CHOICES}
            sx={{ width: "25em" }}
        />
        <AutocompleteArrayInput
            source="observation_notification_status_list"
            label="Statuses for observation notifications"
            choices={OBSERVATION_STATUS_CHOICES}
            sx={{ width: "25em" }}
        />
        <NumberInput
            source="observation_notification_min_priority"
            label="Minimum priority for observation notifications"
            step={1}
            min={1}
            max={99}
            sx={{ width: "25em" }}
        />
    </Stack>
);

export const areNotificationsVisible = (product_group: any) =>
    Boolean(
        (feature_email() && product_group.notification_email_to) ||
        product_group.notification_ms_teams_webhook ||
        product_group.notification_slack_webhook ||
        product_group.observation_notification_min_severity ||
        (product_group.observation_notification_status_list &&
            product_group.observation_notification_status_list.length > 0) ||
        product_group.observation_notification_min_priority
    );

export const NotificationsFields = () => {
    const product_group: any = useRecordContext();
    if (!product_group) {
        return null;
    }

    return (
        <Stack spacing={1}>
            {feature_email() && product_group.notification_email_to && (
                <Labeled label="Email">
                    <TextField source="notification_email_to" />
                </Labeled>
            )}
            {product_group.notification_ms_teams_webhook && (
                <Labeled label="MS Teams">
                    <TextField source="notification_ms_teams_webhook" />
                </Labeled>
            )}
            {product_group.notification_slack_webhook && (
                <Labeled label="Slack">
                    <TextField source="notification_slack_webhook" />
                </Labeled>
            )}
            {product_group.observation_notification_min_severity && (
                <Labeled label="Minimum severity for observation notifications">
                    <TextField source="observation_notification_min_severity" />
                </Labeled>
            )}
            {product_group.observation_notification_status_list &&
                product_group.observation_notification_status_list.length > 0 && (
                    <Labeled label="Statuses for observation notifications">
                        <TextArrayField source="observation_notification_status_list" />
                    </Labeled>
                )}
            {product_group.observation_notification_min_priority && (
                <Labeled label="Minimum priority for observation notifications">
                    <TextField source="observation_notification_min_priority" />
                </Labeled>
            )}
        </Stack>
    );
};
