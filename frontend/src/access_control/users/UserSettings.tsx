import NotificationsIcon from "@mui/icons-material/Notifications";
import PersonIcon from "@mui/icons-material/Person";
import { Divider, FormControl, FormControlLabel, Paper, Radio, RadioGroup, Stack, Typography } from "@mui/material";
import { Fragment, ReactNode, useEffect, useState } from "react";
import { BooleanInput, Form, SaveButton, Title, useNotify, useTheme } from "react-admin";
import { useWatch } from "react-hook-form";

import Toolbar from "../../commons/custom_fields/Toolbar";
import WebhookTestButton from "../../commons/custom_fields/WebhookTestButton";
import { validate_255, validate_2048 } from "../../commons/custom_validators";
import { is_oidc_user } from "../../commons/functions";
import { TextInputExtraWide } from "../../commons/layout/themes";
import {
    METRICS_TIMESPAN_7_DAYS,
    METRICS_TIMESPAN_30_DAYS,
    METRICS_TIMESPAN_90_DAYS,
    METRICS_TIMESPAN_365_DAYS,
} from "../../commons/types";
import ProductNotificationSettings from "../../notifications/product_notifications/ProductNotificationSettings";
import {
    NotificationSettings,
    ThemePreference,
    getSettingListSize,
    getSettingMetricsTimespan,
    getSettingNotifications,
    getSettingPackageInfoPreference,
    getSettingRowsPerPage,
    getSettingTheme,
    loadSettingNotifications,
    resolveTheme,
    saveSettingListSize,
    saveSettingNotifications,
    saveSettingPackageInfoPreference,
    saveSettingRowsPerPage,
    saveSettingTheme,
    saveSettingsMetricsTimespan,
    validateNotificationSettings,
} from "./functions";

type NotificationChannelRowProps = {
    activeSource: string;
    activeLabel: string;
    children: (readOnly: boolean) => ReactNode;
};

// The flag of the channel decides whether its email address or webhook URL can be edited. The
// field is set to readOnly and not to disabled, otherwise react-hook-form would remove its value
// from the submitted data and the stored value would be cleared.
const NotificationChannelRow = ({ activeSource, activeLabel, children }: NotificationChannelRowProps) => {
    const active = useWatch({ name: activeSource });

    return (
        <Stack direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
            <BooleanInput source={activeSource} label={activeLabel} sx={{ width: "10em" }} />
            {children(!active)}
        </Stack>
    );
};

const UserSettings = () => {
    const [, setTheme] = useTheme();
    const notify = useNotify();
    const [notifications, setNotifications] = useState<NotificationSettings>(getSettingNotifications);
    // The form is only initialized from defaultValues when it is mounted, so it is remounted
    // when the settings have been loaded from the API or have been saved
    const [formKey, setFormKey] = useState(0);

    useEffect(() => {
        let outdated = false;

        loadSettingNotifications()
            .then((values) => {
                if (!outdated) {
                    setNotifications(values);
                    setFormKey((key) => key + 1);
                }
            })
            .catch(() => {
                // The values from the local storage are kept
            });

        return () => {
            outdated = true;
        };
    }, []);

    async function saveNotifications(values: any) {
        try {
            setNotifications(
                await saveSettingNotifications({
                    email: values.email ?? "",
                    notification_email_active: values.notification_email_active ?? false,
                    notification_ms_teams_webhook: values.notification_ms_teams_webhook ?? "",
                    notification_ms_teams_active: values.notification_ms_teams_active ?? false,
                    notification_slack_webhook: values.notification_slack_webhook ?? "",
                    notification_slack_active: values.notification_slack_active ?? false,
                })
            );
            setFormKey((key) => key + 1);
            notify("Notification settings saved", { type: "success" });
        } catch (error: any) {
            notify(error.message, { type: "warning" });
        }
    }

    useEffect(() => {
        const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
        const handleChange = () => {
            const currentPreference = getSettingTheme() as ThemePreference;
            if (currentPreference === "system") {
                setTheme(resolveTheme("system"));
            }
        };

        mediaQuery.addEventListener("change", handleChange);
        return () => mediaQuery.removeEventListener("change", handleChange);
    }, [setTheme]);

    function setLightTheme() {
        localStorage.setItem("theme", "light");
        saveSettingTheme("light");
        setTheme("light");
    }

    function setDarkTheme() {
        localStorage.setItem("theme", "dark");
        saveSettingTheme("dark");
        setTheme("dark");
    }

    function setSystemTheme() {
        localStorage.setItem("theme", "system");
        saveSettingTheme("system");
        setTheme(resolveTheme("system"));
    }

    return (
        <Fragment>
            <Title title="Settings" />
            <Paper sx={{ marginTop: 2, padding: 2 }}>
                <Typography variant="h6" sx={{ marginBottom: 2, alignItems: "center", display: "flex" }}>
                    <PersonIcon />
                    &nbsp;&nbsp;General settings
                </Typography>
                <Stack sx={{ width: "100%" }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                        Theme
                    </Typography>
                    <FormControl>
                        <RadioGroup defaultValue={getSettingTheme()} name="radio-buttons-group-theme" row autoFocus>
                            <FormControlLabel
                                value="light"
                                control={<Radio />}
                                label="Light"
                                onClick={() => setLightTheme()}
                            />
                            <FormControlLabel
                                value="dark"
                                control={<Radio />}
                                label="Dark"
                                onClick={() => setDarkTheme()}
                            />
                            <FormControlLabel
                                value="system"
                                control={<Radio />}
                                label="System"
                                onClick={() => setSystemTheme()}
                            />
                        </RadioGroup>
                    </FormControl>

                    <Typography variant="subtitle1" sx={{ fontWeight: "bold", marginTop: 2 }}>
                        List size
                    </Typography>
                    <FormControl>
                        <RadioGroup defaultValue={getSettingListSize()} name="radio-buttons-group-list-size" row>
                            <FormControlLabel
                                value="small"
                                control={<Radio />}
                                label="Small"
                                onClick={() => saveSettingListSize("small")}
                            />
                            <FormControlLabel
                                value="medium"
                                control={<Radio />}
                                label="Medium"
                                onClick={() => saveSettingListSize("medium")}
                            />
                        </RadioGroup>
                    </FormControl>

                    <Typography variant="subtitle1" sx={{ fontWeight: "bold", marginTop: 2 }}>
                        Package information preference
                    </Typography>
                    <FormControl>
                        <RadioGroup
                            defaultValue={getSettingPackageInfoPreference()}
                            name="radio-buttons-group-list-size"
                            row
                        >
                            <FormControlLabel
                                value="open/source/insights"
                                control={<Radio />}
                                label="open/source/insights"
                                onClick={() => saveSettingPackageInfoPreference("open/source/insights")}
                            />
                            <FormControlLabel
                                value="ecosyste.ms"
                                control={<Radio />}
                                label="ecosyste.ms"
                                onClick={() => saveSettingPackageInfoPreference("ecosyste.ms")}
                            />
                        </RadioGroup>
                    </FormControl>

                    <Typography variant="subtitle1" sx={{ fontWeight: "bold", marginTop: 2 }}>
                        Metrics Timespan (days)
                    </Typography>
                    <FormControl>
                        <RadioGroup defaultValue={getSettingMetricsTimespan()} name="radio-buttons-group-list-size" row>
                            <FormControlLabel
                                value={METRICS_TIMESPAN_7_DAYS}
                                control={<Radio />}
                                label="7"
                                onClick={() => saveSettingsMetricsTimespan(METRICS_TIMESPAN_7_DAYS)}
                            />
                            <FormControlLabel
                                value={METRICS_TIMESPAN_30_DAYS}
                                control={<Radio />}
                                label="30"
                                onClick={() => saveSettingsMetricsTimespan(METRICS_TIMESPAN_30_DAYS)}
                            />
                            <FormControlLabel
                                value={METRICS_TIMESPAN_90_DAYS}
                                control={<Radio />}
                                label="90"
                                onClick={() => saveSettingsMetricsTimespan(METRICS_TIMESPAN_90_DAYS)}
                            />
                            <FormControlLabel
                                value={METRICS_TIMESPAN_365_DAYS}
                                control={<Radio />}
                                label="365"
                                onClick={() => saveSettingsMetricsTimespan(METRICS_TIMESPAN_365_DAYS)}
                            />
                        </RadioGroup>
                    </FormControl>

                    <Typography variant="subtitle1" sx={{ fontWeight: "bold", marginTop: 2 }}>
                        Rows per page
                    </Typography>
                    <FormControl>
                        <RadioGroup defaultValue={getSettingRowsPerPage()} name="radio-buttons-group-rows-per-page" row>
                            <FormControlLabel
                                value={10}
                                control={<Radio />}
                                label="10"
                                onClick={() => saveSettingRowsPerPage(10)}
                            />
                            <FormControlLabel
                                value={25}
                                control={<Radio />}
                                label="25"
                                onClick={() => saveSettingRowsPerPage(25)}
                            />
                            <FormControlLabel
                                value={50}
                                control={<Radio />}
                                label="50"
                                onClick={() => saveSettingRowsPerPage(50)}
                            />
                            <FormControlLabel
                                value={100}
                                control={<Radio />}
                                label="100"
                                onClick={() => saveSettingRowsPerPage(100)}
                            />
                        </RadioGroup>
                    </FormControl>
                </Stack>
            </Paper>

            <Paper sx={{ marginTop: 2, padding: 2 }}>
                <Typography variant="h6" sx={{ marginBottom: 2, alignItems: "center", display: "flex" }}>
                    <NotificationsIcon />
                    &nbsp;&nbsp;Notifications
                </Typography>
                <Stack sx={{ width: "100%" }}>
                    <ProductNotificationSettings />

                    <Divider flexItem sx={{ marginTop: 2, marginBottom: 2 }} />

                    <Typography variant="subtitle1" sx={{ fontWeight: "bold", marginBottom: 1 }}>
                        Channels
                    </Typography>
                    <Form
                        key={formKey}
                        defaultValues={notifications}
                        validate={validateNotificationSettings}
                        onSubmit={saveNotifications}
                    >
                        <Stack spacing={2}>
                            <NotificationChannelRow activeSource="notification_email_active" activeLabel="Email">
                                {(readOnly) => (
                                    <TextInputExtraWide
                                        source="email"
                                        label="Email address to send notifications to"
                                        validate={validate_255}
                                        readOnly={readOnly || is_oidc_user()}
                                        helperText={
                                            is_oidc_user()
                                                ? "The email address is maintained by the identity provider"
                                                : undefined
                                        }
                                    />
                                )}
                            </NotificationChannelRow>
                            <NotificationChannelRow activeSource="notification_ms_teams_active" activeLabel="MS Teams">
                                {(readOnly) => (
                                    <Fragment>
                                        <TextInputExtraWide
                                            source="notification_ms_teams_webhook"
                                            label="Webhook URL to send notifications to MS Teams"
                                            validate={validate_2048}
                                            readOnly={readOnly}
                                        />
                                        <WebhookTestButton
                                            webhookSource="notification_ms_teams_webhook"
                                            webhookType="msteams"
                                            disabled={readOnly}
                                        />
                                    </Fragment>
                                )}
                            </NotificationChannelRow>
                            <NotificationChannelRow activeSource="notification_slack_active" activeLabel="Slack">
                                {(readOnly) => (
                                    <Fragment>
                                        <TextInputExtraWide
                                            source="notification_slack_webhook"
                                            label="Webhook URL to send notifications to Slack"
                                            validate={validate_2048}
                                            readOnly={readOnly}
                                        />
                                        <WebhookTestButton
                                            webhookSource="notification_slack_webhook"
                                            webhookType="slack"
                                            disabled={readOnly}
                                        />
                                    </Fragment>
                                )}
                            </NotificationChannelRow>
                            <Toolbar>
                                <SaveButton label="Save channels" />
                            </Toolbar>
                        </Stack>
                    </Form>
                </Stack>
            </Paper>
        </Fragment>
    );
};

export default UserSettings;
