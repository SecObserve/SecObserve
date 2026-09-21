import { Stack } from "@mui/material";
import {
    AutocompleteArrayInput,
    Labeled,
    NumberField,
    NumberInput,
    TextArrayField,
    TextField,
    useRecordContext,
} from "react-admin";

import { OBSERVATION_SEVERITY_CHOICES, OBSERVATION_STATUS_CHOICES } from "../../../core/types";
import { SCANNER_TYPE_CHOICES } from "../../../import_observations/types";
import WebhookTestButton from "../../custom_fields/WebhookTestButton";
import { validate_0_999999, validate_255, validate_2048 } from "../../custom_validators";
import { feature_email } from "../../functions";
import { AutocompleteInputMedium, TextInputExtraWide, TextInputWide } from "../../layout/themes";

/** The backend does not accept null for these fields, they have to be sent as an empty string. */
export const transformNotifications = (data: any) => {
    data.base_url_frontend ??= "";
    data.email_from ??= "";
    data.exception_email_to ??= "";
    data.exception_ms_teams_webhook ??= "";
    data.exception_slack_webhook ??= "";
    data.observation_title_notification_email_to ??= "";
    data.observation_title_notification_ms_teams_webhook ??= "";
    data.observation_title_notification_slack_webhook ??= "";
    data.observation_title_notification_min_severity ??= "";
    data.observation_title_notification_parser_type ??= "";
};

export const NotificationsInputs = () => (
    <>
        <TextInputWide
            source="base_url_frontend"
            label="Base URL frontend"
            validate={validate_255}
            helperText="Base URL of the frontend, used to set links in notifications correctly"
            sx={{ marginBottom: 2 }}
        />
        {feature_email() && (
            <TextInputWide
                source="email_from"
                label="Email from"
                validate={validate_255}
                helperText="From address for sending email notifications"
                sx={{ marginBottom: 2 }}
            />
        )}
        {feature_email() && (
            <TextInputExtraWide
                source="exception_email_to"
                label="Comma separated email addresses to send exception notifications"
                validate={validate_255}
            />
        )}
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <TextInputExtraWide
                source="exception_ms_teams_webhook"
                label="MS Teams webhook to send exception notifications"
                validate={validate_2048}
            />
            <WebhookTestButton webhookSource="exception_ms_teams_webhook" webhookType="msteams" />
        </Stack>
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <TextInputExtraWide
                source="exception_slack_webhook"
                label="Slack webhook to send exception notifications"
                validate={validate_2048}
            />
            <WebhookTestButton webhookSource="exception_slack_webhook" webhookType="slack" />
        </Stack>
        <NumberInput
            source="exception_rate_limit"
            label="Exception rate limit"
            min={0}
            step={1}
            validate={validate_0_999999}
            helperText="Timedelta in seconds when to send the same exception the next time"
            sx={{ marginBottom: 2 }}
        />
        {feature_email() && (
            <TextInputExtraWide
                source="observation_title_notification_email_to"
                label="Comma separated email to addresses to send observation title notifications"
                validate={validate_255}
            />
        )}
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <TextInputExtraWide
                source="observation_title_notification_ms_teams_webhook"
                label="Webhook URL to send observation title notifications to MS Teams"
                validate={validate_2048}
            />
            <WebhookTestButton webhookSource="observation_title_notification_ms_teams_webhook" webhookType="msteams" />
        </Stack>
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <TextInputExtraWide
                source="observation_title_notification_slack_webhook"
                label="Webhook URL to send observation title notifications to Slack"
                validate={validate_2048}
            />
            <WebhookTestButton webhookSource="observation_title_notification_slack_webhook" webhookType="slack" />
        </Stack>
        <AutocompleteInputMedium
            source="observation_title_notification_min_severity"
            label="Minimum severity for observation title notifications"
            choices={OBSERVATION_SEVERITY_CHOICES}
            sx={{ width: "27em" }}
        />
        <AutocompleteArrayInput
            source="observation_title_notification_status_list"
            label="Statuses for observation title notifications"
            choices={OBSERVATION_STATUS_CHOICES}
            sx={{ width: "27em" }}
        />
        <NumberInput
            source="observation_title_notification_min_priority"
            label="Minimum priority for observation title notifications"
            step={1}
            min={1}
            max={99}
            sx={{ width: "27em" }}
        />
        <AutocompleteInputMedium
            source="observation_title_notification_parser_type"
            label="Parser type for observation title notifications"
            choices={SCANNER_TYPE_CHOICES}
            sx={{ width: "27em" }}
        />
    </>
);

export const NotificationsFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <Stack spacing={2}>
            {settings.base_url_frontend && (
                <Labeled label="Base URL frontend">
                    <TextField source="base_url_frontend" />
                </Labeled>
            )}
            {feature_email() && settings.email_from && (
                <Labeled label="Email from">
                    <TextField source="email_from" />
                </Labeled>
            )}
            {feature_email() && settings.exception_email_to && (
                <Labeled label="Exception email to">
                    <TextField source="exception_email_to" />
                </Labeled>
            )}
            {settings.exception_ms_teams_webhook && (
                <Labeled label="Exception MS Teams webhook">
                    <TextField source="exception_ms_teams_webhook" />
                </Labeled>
            )}
            {settings.exception_slack_webhook && (
                <Labeled label="Exception Slack webhook">
                    <TextField source="exception_slack_webhook" />
                </Labeled>
            )}
            <Labeled label="Exception rate limit">
                <NumberField source="exception_rate_limit" />
            </Labeled>
            {feature_email() && settings.observation_title_notification_email_to && (
                <Labeled label="Email to addresses for observation title notifications">
                    <TextField source="observation_title_notification_email_to" />
                </Labeled>
            )}
            {settings.observation_title_notification_ms_teams_webhook && (
                <Labeled label="MS Teams webhook for observation title notifications">
                    <TextField source="observation_title_notification_ms_teams_webhook" />
                </Labeled>
            )}
            {settings.observation_title_notification_slack_webhook && (
                <Labeled label="Slack webhook for observation title notifications">
                    <TextField source="observation_title_notification_slack_webhook" />
                </Labeled>
            )}
            {settings.observation_title_notification_min_severity && (
                <Labeled label="Minimum severity for observation title notifications">
                    <TextField source="observation_title_notification_min_severity" />
                </Labeled>
            )}
            {settings.observation_title_notification_status_list &&
                settings.observation_title_notification_status_list.length > 0 && (
                    <Labeled label="Statuses for observation title notifications">
                        <TextArrayField source="observation_title_notification_status_list" />
                    </Labeled>
                )}
            {settings.observation_title_notification_min_priority && (
                <Labeled label="Minimum priority for observation title notifications">
                    <TextField source="observation_title_notification_min_priority" />
                </Labeled>
            )}
            {settings.observation_title_notification_parser_type && (
                <Labeled label="Parser type for observation title notifications">
                    <TextField source="observation_title_notification_parser_type" />
                </Labeled>
            )}
        </Stack>
    );
};
