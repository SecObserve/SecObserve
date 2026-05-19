import { Divider, Grid, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    AutocompleteArrayInput,
    BooleanInput,
    Edit,
    FormDataConsumer,
    NumberInput,
    RadioButtonGroupInput,
    SaveButton,
    SimpleForm,
    Toolbar,
} from "react-admin";

import settings from ".";
import {
    validate_0_23,
    validate_0_59,
    validate_0_999999,
    validate_1_4096,
    validate_1_999999,
    validate_255,
    validate_2048,
} from "../../commons/custom_validators";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium, TextInputExtraWide, TextInputWide } from "../../commons/layout/themes";
import { OBSERVATION_SEVERITY_CHOICES, OBSERVATION_STATUS_CHOICES } from "../../core/types";
import { SCANNER_TYPE_CHOICES } from "../../import_observations/types";
import { feature_email } from "../functions";
import { VEX_JUSTIFICATION_TYPE_CHOICES } from "../types";

const CustomToolbar = () => {
    return (
        <Toolbar sx={{ display: "flex", justifyContent: "space-between" }}>
            <SaveButton />
        </Toolbar>
    );
};

const SettingsEdit = () => {
    const transform = (data: any) => {
        data.internal_users ??= "";
        data.branch_housekeeping_exempt_branches ??= "";
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
        return data;
    };

    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Edit redirect="show" mutationMode="pessimistic" transform={transform}>
                <SimpleForm warnWhenUnsavedChanges toolbar={<CustomToolbar />}>
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
                        Authentication
                    </Typography>
                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <NumberInput
                                autoFocus
                                source="jwt_validity_duration_user"
                                label="JWT validity duration user (hours)"
                                min={0}
                                step={1}
                                validate={validate_0_999999}
                                helperText="Validity duration of JWT tokens for regular users in hours"
                                sx={{ marginBottom: 2 }}
                            />
                        </Grid>
                        <Grid size={3}>
                            <NumberInput
                                source="jwt_validity_duration_superuser"
                                label="JWT validity duration superuser (hours)"
                                min={0}
                                step={1}
                                validate={validate_0_999999}
                                helperText="Validity duration of JWT tokens for superusers in hours"
                                sx={{ marginBottom: 2 }}
                            />
                        </Grid>
                    </Grid>
                    <TextInputWide
                        source="internal_users"
                        label="Internal users"
                        validate={validate_255}
                        helperText="Comma separated list of email regular expressions to identify internal users"
                        sx={{ marginBottom: 2 }}
                    />
                    <NumberInput
                        source="oidc_clock_skew"
                        label="OIDC clock skew (seconds)"
                        min={0}
                        step={1}
                        validate={validate_0_999999}
                        helperText="Time margin in seconds for checks of issued at, not before and expiration of OIDC tokens"
                        sx={{ marginBottom: 2 }}
                    />

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
                        Features
                    </Typography>
                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <BooleanInput
                                    source="feature_vex"
                                    label="VEX"
                                    helperText="Export and import VEX documents in various formats"
                                />
                            </Stack>
                        </Grid>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <FormDataConsumer>
                                    {({ formData }) =>
                                        formData.feature_vex && (
                                            <RadioButtonGroupInput
                                                source="vex_justification_style"
                                                label="VEX justification style"
                                                choices={VEX_JUSTIFICATION_TYPE_CHOICES}
                                            />
                                        )
                                    }
                                </FormDataConsumer>
                            </Stack>
                        </Grid>
                    </Grid>
                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <BooleanInput
                                    source="feature_disable_user_login"
                                    label="Disable user login"
                                    helperText="Do not show user and password fields if OIDC login is enabled"
                                />
                                <BooleanInput
                                    source="feature_general_rules_need_approval"
                                    label="General rules need approval"
                                />
                                <BooleanInput source="feature_license_management" label="Enable license management" />
                            </Stack>
                        </Grid>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <BooleanInput
                                    source="feature_automatic_api_import"
                                    label="Enable automatic API imports"
                                />
                                <BooleanInput
                                    source="feature_automatic_osv_scanning"
                                    label="Enable automatic OSV scanning"
                                />
                                <BooleanInput
                                    source="observation_count_from_metrics"
                                    label="Calculate observation count from metrics"
                                />
                            </Stack>
                        </Grid>
                    </Grid>
                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <BooleanInput
                                    source="feature_exploit_information"
                                    label="Enable exploit enrichment from cvss-bt"
                                />
                            </Stack>
                        </Grid>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <FormDataConsumer>
                                    {({ formData }) =>
                                        formData.feature_exploit_information && (
                                            <NumberInput
                                                source="exploit_information_max_age_years"
                                                label="Maximum age of CVEs for enrichment in years"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                            />
                                        )
                                    }
                                </FormDataConsumer>
                            </Stack>
                        </Grid>
                    </Grid>
                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <BooleanInput
                                    source="feature_cross_scanner_deduplication"
                                    label="Enable cross scanner deduplication"
                                />
                            </Stack>
                        </Grid>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <NumberInput
                                    source="risk_acceptance_expiry_days"
                                    label="Risk acceptance expiry (days)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_999999}
                                    helperText="Days before risk acceptance expires, 0 means no expiry"
                                    sx={{ marginBottom: 2 }}
                                />
                            </Stack>
                        </Grid>
                    </Grid>

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
                        Housekeeping for branches
                    </Typography>

                    <BooleanInput
                        source="branch_housekeeping_active"
                        label="Branch housekeeping active"
                        helperText="Delete inactive branches"
                        sx={{ marginBottom: 2 }}
                    />
                    <FormDataConsumer>
                        {({ formData }) =>
                            formData.branch_housekeeping_active && (
                                <Grid container spacing={2} width={"100%"}>
                                    <Grid size={3}>
                                        <NumberInput
                                            source="branch_housekeeping_keep_inactive_days"
                                            label="Branch housekeeping keep inactive (days)"
                                            min={0}
                                            step={1}
                                            validate={validate_0_999999}
                                            helperText="Days before incative branches and their observations are deleted"
                                            sx={{ marginBottom: 2 }}
                                        />
                                    </Grid>
                                    <Grid size={3}>
                                        <TextInputWide
                                            source="branch_housekeeping_exempt_branches"
                                            label="Branch housekeeping exempt branches"
                                            validate={validate_255}
                                            helperText="Regular expression which branches to exempt from deletion"
                                            sx={{ marginBottom: 2 }}
                                        />
                                    </Grid>
                                </Grid>
                            )
                        }
                    </FormDataConsumer>

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
                        Notifications
                    </Typography>
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
                    <TextInputExtraWide
                        source="exception_ms_teams_webhook"
                        label="MS Teams webhook to send exception notifications"
                        validate={validate_2048}
                    />
                    <TextInputExtraWide
                        source="exception_slack_webhook"
                        label="Slack webhook to send exception notifications"
                        validate={validate_2048}
                    />
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
                    <TextInputExtraWide
                        source="observation_title_notification_ms_teams_webhook"
                        label="Webhook URL to send observation title notifications to MS Teams"
                        validate={validate_2048}
                    />
                    <TextInputExtraWide
                        source="observation_title_notification_slack_webhook"
                        label="Webhook URL to send observation title notifications to Slack"
                        validate={validate_2048}
                    />
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

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
                        Security gates
                    </Typography>
                    <BooleanInput
                        source="security_gate_active"
                        label="Security gates active"
                        helperText="Are security gates activated?"
                        sx={{ marginBottom: 2 }}
                    />
                    <FormDataConsumer>
                        {({ formData }) =>
                            formData.security_gate_active && (
                                <Grid container spacing={2} width={"100%"}>
                                    <Grid size={3}>
                                        <Stack spacing={2}>
                                            <NumberInput
                                                source="security_gate_threshold_critical"
                                                label="Threshold critical"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                                helperText="Number of critical observations that must not be exceeded"
                                                sx={{ marginBottom: 2 }}
                                            />
                                            <NumberInput
                                                source="security_gate_threshold_high"
                                                label="Threshold high"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                                helperText="Number of high observations that must not be exceeded"
                                                sx={{ marginBottom: 2 }}
                                            />
                                            <NumberInput
                                                source="security_gate_threshold_medium"
                                                label="Threshold medium"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                                helperText="Number of medium observations that must not be exceeded"
                                                sx={{ marginBottom: 2 }}
                                            />
                                        </Stack>
                                    </Grid>
                                    <Grid size={3}>
                                        <Stack spacing={2}>
                                            <NumberInput
                                                source="security_gate_threshold_low"
                                                label="Threshold low"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                                helperText="Number of low observations that must not be exceeded"
                                                sx={{ marginBottom: 2 }}
                                            />
                                            <NumberInput
                                                source="security_gate_threshold_none"
                                                label="Threshold none"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                                helperText="Number of none observations that must not be exceeded"
                                                sx={{ marginBottom: 2 }}
                                            />
                                            <NumberInput
                                                source="security_gate_threshold_unknown"
                                                label="Threshold unknown"
                                                min={0}
                                                step={1}
                                                validate={validate_0_999999}
                                                helperText="Number of unknown observations that must not be exceeded"
                                                sx={{ marginBottom: 2 }}
                                            />
                                        </Stack>
                                    </Grid>
                                </Grid>
                            )
                        }
                    </FormDataConsumer>

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 2 }}>
                        Password validation for non-OIDC users
                    </Typography>

                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <NumberInput
                                    source="password_validator_minimum_length"
                                    label="Minimum length"
                                    min={1}
                                    step={1}
                                    validate={validate_1_4096}
                                    helperText="Validates that the password is of a minimum length."
                                    sx={{ marginBottom: 1 }}
                                />
                                <BooleanInput
                                    source="password_validator_attribute_similarity"
                                    label="Attribute similarity"
                                    helperText="Validates that the password is sufficiently different from certain attributes of the user."
                                    sx={{ marginBottom: 1 }}
                                />
                            </Stack>
                        </Grid>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <BooleanInput
                                    source="password_validator_common_passwords"
                                    label="Common passwords"
                                    helperText="Validates that the password is not a common password."
                                    sx={{ marginBottom: 1 }}
                                />
                                <BooleanInput
                                    source="password_validator_not_numeric"
                                    label="Not entirely numeric"
                                    helperText="Validate that the password is not entirely numeric."
                                    sx={{ marginBottom: 1 }}
                                />
                            </Stack>
                        </Grid>
                    </Grid>

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />
                    <Typography variant="h6" sx={{ marginBottom: 3 }}>
                        Background tasks
                    </Typography>

                    <Typography variant="body2" sx={{ marginBottom: 3 }}>
                        The settings in this section require a restart of the SecObserve backend to take effect.
                    </Typography>

                    <NumberInput
                        source="background_product_metrics_interval_minutes"
                        label="Product metrics interval (minutes)"
                        min={0}
                        step={1}
                        validate={validate_0_999999}
                        helperText="Calculate product metrics every x minutes"
                        sx={{ marginBottom: 4 }}
                    />

                    <Grid container spacing={2} width={"100%"}>
                        <Grid size={3}>
                            <Stack spacing={2}>
                                <NumberInput
                                    source="risk_acceptance_expiry_crontab_hour"
                                    label="Risk acceptance expiry crontab (hour)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_23}
                                    // helperText="Hour crontab expression for checking risk acceptance expiry (UTC)"
                                />

                                <FormDataConsumer>
                                    {({ formData }) =>
                                        formData.feature_license_management && (
                                            <NumberInput
                                                source="license_import_crontab_hour"
                                                label="License import crontab (hour)"
                                                min={0}
                                                step={1}
                                                validate={validate_0_23}
                                                // helperText="Hour crontab expression for license imports (UTC)"
                                            />
                                        )
                                    }
                                </FormDataConsumer>
                                <NumberInput
                                    source="branch_housekeeping_crontab_hour"
                                    label="Branch housekeeping crontab (hour)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_23}
                                    // helperText="Hour crontab expression for branch housekeeping (UTC)"
                                />
                                <NumberInput
                                    source="background_epss_import_crontab_hour"
                                    label="EPSS and exploit import crontab (hour)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_23}
                                    // helperText="Hour crontab expression for EPSS import (UTC)"
                                />
                                <FormDataConsumer>
                                    {({ formData }) =>
                                        (formData.feature_automatic_api_import ||
                                            formData.feature_automatic_osv_scanning) && (
                                            <NumberInput
                                                source="api_import_crontab_hour"
                                                label="API import and OSV scanning crontab (hour)"
                                                min={0}
                                                step={1}
                                                validate={validate_0_23}
                                                // helperText="Hour crontab expression for API imports (UTC)"
                                            />
                                        )
                                    }
                                </FormDataConsumer>
                                <NumberInput
                                    source="periodic_task_max_entries"
                                    label="Number of entries of Periodic Task to keep per task"
                                    min={1}
                                    step={1}
                                    validate={validate_1_999999}
                                />
                            </Stack>
                        </Grid>

                        <Grid size={3}>
                            <Stack spacing={2}>
                                <NumberInput
                                    source="risk_acceptance_expiry_crontab_minute"
                                    label="Risk acceptance expiry crontab (minute)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_59}
                                    // helperText="Minute crontab expression for checking risk acceptance expiry"
                                />

                                <FormDataConsumer>
                                    {({ formData }) =>
                                        formData.feature_license_management && (
                                            <NumberInput
                                                source="license_import_crontab_minute"
                                                label="License import crontab (minute)"
                                                min={0}
                                                step={1}
                                                validate={validate_0_59}
                                                // helperText="Minute crontab expression for license imports"
                                            />
                                        )
                                    }
                                </FormDataConsumer>
                                <NumberInput
                                    source="branch_housekeeping_crontab_minute"
                                    label="Branch housekeeping crontab (minute)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_59}
                                    // helperText="Minute crontab expression for branch housekeeping"
                                />
                                <NumberInput
                                    source="background_epss_import_crontab_minute"
                                    label="EPSS and exploit import crontab (minute)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_59}
                                    // helperText="Minute crontab expression for EPSS import"
                                />
                                <FormDataConsumer>
                                    {({ formData }) =>
                                        (formData.feature_automatic_api_import ||
                                            formData.feature_automatic_osv_scanning) && (
                                            <NumberInput
                                                source="api_import_crontab_minute"
                                                label="API import and OSV scanning crontab (minute)"
                                                min={0}
                                                step={1}
                                                validate={validate_0_59}
                                                // helperText="Minute crontab expression for API imports"
                                            />
                                        )
                                    }
                                </FormDataConsumer>
                            </Stack>
                        </Grid>
                    </Grid>
                </SimpleForm>
            </Edit>
        </Fragment>
    );
};

export default SettingsEdit;
