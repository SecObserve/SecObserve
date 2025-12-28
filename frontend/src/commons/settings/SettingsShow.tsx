import { Box, Grid, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import { BooleanField, EditButton, Labeled, NumberField, Show, TextField, TopToolbar, WithRecord } from "react-admin";

import settings from ".";
import ListHeader from "../../commons/layout/ListHeader";
import { feature_email } from "../functions";
import JWTSecretReset from "./JWTSecretReset";

const ShowActions = () => {
    return (
        <TopToolbar>
            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <JWTSecretReset />
                <EditButton />
            </Stack>
        </TopToolbar>
    );
};

const SettingsShowComponent = () => {
    return (
        <WithRecord
            render={(settings) => (
                <Box width={"100%"}>
                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Authentication
                        </Typography>
                        <Grid container spacing={2} width={"100%"}>
                            <Grid size={3}>
                                <Labeled label="JWT validity duration user (hours)">
                                    <NumberField source="jwt_validity_duration_user" />
                                </Labeled>
                            </Grid>
                            <Grid size={3}>
                                <Labeled label="JWT validity duration superuser (hours)">
                                    <NumberField source="jwt_validity_duration_superuser" />
                                </Labeled>
                            </Grid>
                            <Grid size={6} />
                        </Grid>
                        {settings.internal_users && (
                            <Labeled label="Internal users">
                                <TextField source="internal_users" />
                            </Labeled>
                        )}
                        {settings.oidc_clock_skew > 0 && (
                            <Labeled label="OIDC clock skew (seconds)">
                                <NumberField source="oidc_clock_skew" />
                            </Labeled>
                        )}
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Features
                        </Typography>
                        <Grid container spacing={2} width={"100%"} sx={{ marginBottom: 2 }}>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="VEX">
                                        <BooleanField source="feature_vex" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    {settings.feature_vex && (
                                        <Labeled label="VEX justification style">
                                            <TextField source="vex_justification_style" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Grid>
                        </Grid>
                        <Grid container spacing={2} width={"100%"} sx={{ marginBottom: 2 }}>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Disable user login">
                                        <BooleanField source="feature_disable_user_login" />
                                    </Labeled>
                                    <Labeled label="General rules need approval">
                                        <BooleanField source="feature_general_rules_need_approval" />
                                    </Labeled>
                                    <Labeled label="Enable license management">
                                        <BooleanField source="feature_license_management" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Enable automatic API imports">
                                        <BooleanField source="feature_automatic_api_import" />
                                    </Labeled>
                                    <Labeled label="Enable automatic OSV scanning">
                                        <BooleanField source="feature_automatic_osv_scanning" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                        </Grid>
                        <Grid container spacing={2} width={"100%"} sx={{ marginBottom: 2 }}>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Enable exploit enrichment from cvss-bt">
                                        <BooleanField source="feature_exploit_information" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    {settings.feature_exploit_information && (
                                        <Labeled label="Maximum age of CVEs for enrichment in years">
                                            <NumberField source="exploit_information_max_age_years" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Grid>
                        </Grid>
                        <Labeled label="Risk acceptance expiry (days)">
                            <NumberField source="risk_acceptance_expiry_days" />
                        </Labeled>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Housekeeping for branches
                        </Typography>
                        <Labeled label="Branch housekeeping active">
                            <BooleanField source="branch_housekeeping_active" sx={{ marginBottom: 1 }} />
                        </Labeled>
                        {settings.branch_housekeeping_active && (
                            <Grid container spacing={2} width={"100%"}>
                                <Grid size={3}>
                                    <Labeled label="Branch housekeeping keep inactive (days)">
                                        <NumberField source="branch_housekeeping_keep_inactive_days" />
                                    </Labeled>
                                </Grid>
                                <Grid size={3}>
                                    {settings.branch_housekeeping_exempt_branches && (
                                        <Labeled label="Branch housekeeping exempt branches">
                                            <TextField source="branch_housekeeping_exempt_branches" />
                                        </Labeled>
                                    )}
                                </Grid>
                            </Grid>
                        )}
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Integrations
                        </Typography>
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
                        </Stack>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Security gates
                        </Typography>
                        <Labeled label="Security gates active" sx={{ marginBottom: 2 }}>
                            <BooleanField source="security_gate_active" />
                        </Labeled>
                        {settings.security_gate_active && (
                            <Grid container spacing={2} width={"100%"}>
                                <Grid size={3}>
                                    <Stack spacing={2}>
                                        <Labeled label="Threshold critical">
                                            <NumberField source="security_gate_threshold_critical" />
                                        </Labeled>
                                        <Labeled label="Threshold high">
                                            <NumberField source="security_gate_threshold_high" />
                                        </Labeled>
                                        <Labeled label="Threshold medium">
                                            <NumberField source="security_gate_threshold_medium" />
                                        </Labeled>
                                    </Stack>
                                </Grid>
                                <Grid size={3}>
                                    <Stack spacing={2}>
                                        <Labeled label="Threshold low">
                                            <NumberField source="security_gate_threshold_low" />
                                        </Labeled>
                                        <Labeled label="Threshold none">
                                            <NumberField source="security_gate_threshold_none" />
                                        </Labeled>
                                        <Labeled label="Threshold unknown">
                                            <NumberField source="security_gate_threshold_unknown" />
                                        </Labeled>
                                    </Stack>
                                </Grid>
                            </Grid>
                        )}
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Password validation for non-OIDC users
                        </Typography>

                        <Grid container spacing={2} width={"100%"}>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Minimum length">
                                        <NumberField source="password_validator_minimum_length" />
                                    </Labeled>
                                    <Labeled label="Attribute similarity">
                                        <BooleanField source="password_validator_attribute_similarity" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Common passwords">
                                        <BooleanField source="password_validator_common_passwords" />
                                    </Labeled>
                                    <Labeled label="Not entirely numeric">
                                        <BooleanField source="password_validator_not_numeric" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                        </Grid>
                    </Paper>

                    <Paper sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Background tasks
                        </Typography>

                        <Labeled label="Product metrics interval (minutes)" sx={{ marginBottom: 2 }}>
                            <NumberField source="background_product_metrics_interval_minutes" />
                        </Labeled>

                        <Grid container spacing={2} width={"100%"}>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Risk acceptance expiry crontab (hour/UTC)">
                                        <NumberField source="risk_acceptance_expiry_crontab_hour" />
                                    </Labeled>
                                    {settings.feature_license_management && (
                                        <Labeled label="License import crontab (hour/UTC)">
                                            <NumberField source="license_import_crontab_hour" />
                                        </Labeled>
                                    )}
                                    <Labeled label="Branch housekeeping crontab (hour/UTC)">
                                        <NumberField source="branch_housekeeping_crontab_hour" />
                                    </Labeled>
                                    <Labeled label="EPSS and exploit import crontab (hour/UTC)">
                                        <NumberField source="background_epss_import_crontab_hour" />
                                    </Labeled>
                                    {(settings.feature_automatic_api_import ||
                                        settings.feature_automatic_osv_scanning) && (
                                        <Labeled label="API import and OSV scanning crontab (hour/UTC)">
                                            <NumberField source="api_import_crontab_hour" />
                                        </Labeled>
                                    )}
                                    <Labeled label="Number of entries of Periodic Task to keep per task">
                                        <NumberField source="periodic_task_max_entries" />
                                    </Labeled>
                                </Stack>
                            </Grid>
                            <Grid size={3}>
                                <Stack spacing={2}>
                                    <Labeled label="Risk acceptance expiry crontab (minute)">
                                        <NumberField source="risk_acceptance_expiry_crontab_minute" />
                                    </Labeled>
                                    {settings.feature_license_management && (
                                        <Labeled label="License import crontab (minute)">
                                            <NumberField source="license_import_crontab_minute" />
                                        </Labeled>
                                    )}
                                    <Labeled label="Branch housekeeping crontab (minute)">
                                        <NumberField source="branch_housekeeping_crontab_minute" />
                                    </Labeled>
                                    <Labeled label="EPSS and exploit import crontab (minutes)">
                                        <NumberField source="background_epss_import_crontab_minute" />
                                    </Labeled>
                                    {(settings.feature_automatic_api_import ||
                                        settings.feature_automatic_osv_scanning) && (
                                        <Labeled label="API import and OSV scanning crontab (minute)">
                                            <NumberField source="api_import_crontab_minute" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Grid>
                        </Grid>
                    </Paper>
                </Box>
            )}
        />
    );
};
const SettingsShow = () => {
    return (
        <Fragment>
            <ListHeader icon={settings.icon} title="Settings" />
            <Show component={SettingsShowComponent} actions={<ShowActions />}>
                <Fragment />
            </Show>
        </Fragment>
    );
};

export default SettingsShow;
