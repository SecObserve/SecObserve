import PublicIcon from "@mui/icons-material/Public";
import { Chip, Grid, Stack, Typography } from "@mui/material";
import { FormDataConsumer, Labeled, NumberField, NumberInput, useRecordContext } from "react-admin";

import { validate_0_23, validate_0_59, validate_0_999999, validate_1_999999 } from "../../custom_validators";
import { settings_background_tasks_time_zone } from "../../functions";

const TimeZoneChip = () => {
    const time_zone = settings_background_tasks_time_zone();
    const offset = new Intl.DateTimeFormat("en-US", { timeZone: time_zone, timeZoneName: "longOffset" })
        .formatToParts(new Date())
        .find((part) => part.type === "timeZoneName")?.value;
    return (
        <Chip
            icon={<PublicIcon />}
            label={`${time_zone} · ${offset === "GMT" ? "UTC+00:00" : offset?.replace("GMT", "UTC")}`}
            title="The hours and minutes of the background tasks are in this time zone, set with BACKGROUND_TASKS_TIME_ZONE"
            size="small"
            variant="outlined"
            sx={{ display: "flex", width: "fit-content", marginBottom: 2 }}
        />
    );
};

export const BackgroundTasksInputs = () => (
    <>
        <TimeZoneChip />
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

        <Grid container spacing={2} sx={{ width: "100%" }}>
            <Grid size={3}>
                <Stack spacing={2}>
                    <NumberInput
                        source="risk_acceptance_expiry_crontab_hour"
                        label="Risk acceptance expiry crontab (hour)"
                        min={0}
                        step={1}
                        validate={validate_0_23}
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
                                />
                            )
                        }
                    </FormDataConsumer>
                    <NumberInput
                        source="branch_housekeeping_crontab_hour"
                        label="Housekeeping crontab (hour)"
                        min={0}
                        step={1}
                        validate={validate_0_23}
                    />
                    <NumberInput
                        source="background_epss_import_crontab_hour"
                        label="EPSS and exploit import crontab (hour)"
                        min={0}
                        step={1}
                        validate={validate_0_23}
                    />
                    <FormDataConsumer>
                        {({ formData }) =>
                            (formData.feature_automatic_api_import || formData.feature_automatic_osv_scanning) && (
                                <NumberInput
                                    source="api_import_crontab_hour"
                                    label="API import, OSV and VulnerableCode scanning crontab (hour)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_23}
                                />
                            )
                        }
                    </FormDataConsumer>
                    <NumberInput
                        source="periodic_task_max_entries"
                        label="Number of entries of Tracked Tasks to keep per task"
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
                                />
                            )
                        }
                    </FormDataConsumer>
                    <NumberInput
                        source="branch_housekeeping_crontab_minute"
                        label="Housekeeping crontab (minute)"
                        min={0}
                        step={1}
                        validate={validate_0_59}
                    />
                    <NumberInput
                        source="background_epss_import_crontab_minute"
                        label="EPSS and exploit import crontab (minute)"
                        min={0}
                        step={1}
                        validate={validate_0_59}
                    />
                    <FormDataConsumer>
                        {({ formData }) =>
                            (formData.feature_automatic_api_import || formData.feature_automatic_osv_scanning) && (
                                <NumberInput
                                    source="api_import_crontab_minute"
                                    label="API import, OSV and VulnerableCode scanning crontab (minute)"
                                    min={0}
                                    step={1}
                                    validate={validate_0_59}
                                />
                            )
                        }
                    </FormDataConsumer>
                </Stack>
            </Grid>
        </Grid>
    </>
);

export const BackgroundTasksFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <TimeZoneChip />
            <Labeled label="Product metrics interval (minutes)" sx={{ marginBottom: 2 }}>
                <NumberField source="background_product_metrics_interval_minutes" />
            </Labeled>

            <Grid container spacing={2} sx={{ width: "100%" }}>
                <Grid size={3}>
                    <Stack spacing={2}>
                        <Labeled label="Risk acceptance expiry crontab (hour)">
                            <NumberField source="risk_acceptance_expiry_crontab_hour" />
                        </Labeled>
                        {settings.feature_license_management && (
                            <Labeled label="License import crontab (hour)">
                                <NumberField source="license_import_crontab_hour" />
                            </Labeled>
                        )}
                        <Labeled label="Housekeeping crontab (hour)">
                            <NumberField source="branch_housekeeping_crontab_hour" />
                        </Labeled>
                        <Labeled label="EPSS and exploit import crontab (hour)">
                            <NumberField source="background_epss_import_crontab_hour" />
                        </Labeled>
                        {(settings.feature_automatic_api_import || settings.feature_automatic_osv_scanning) && (
                            <Labeled label="API import, OSV and VulnerableCode scanning crontab (hour)">
                                <NumberField source="api_import_crontab_hour" />
                            </Labeled>
                        )}
                        <Labeled label="Number of entries of Tracked Tasks to keep per task">
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
                        <Labeled label="Housekeeping crontab (minute)">
                            <NumberField source="branch_housekeeping_crontab_minute" />
                        </Labeled>
                        <Labeled label="EPSS and exploit import crontab (minutes)">
                            <NumberField source="background_epss_import_crontab_minute" />
                        </Labeled>
                        {(settings.feature_automatic_api_import || settings.feature_automatic_osv_scanning) && (
                            <Labeled label="API import, OSV and VulnerableCode scanning crontab (minute)">
                                <NumberField source="api_import_crontab_minute" />
                            </Labeled>
                        )}
                    </Stack>
                </Grid>
            </Grid>
        </>
    );
};
