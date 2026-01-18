import {
    Card,
    CardContent,
    CardHeader,
    FormControl,
    FormControlLabel,
    Radio,
    RadioGroup,
    Stack,
    Typography,
} from "@mui/material";
import { Title, useTheme } from "react-admin";

import {
    METRICS_TIMESPAN_7_DAYS,
    METRICS_TIMESPAN_30_DAYS,
    METRICS_TIMESPAN_90_DAYS,
    METRICS_TIMESPAN_365_DAYS,
} from "../types";
import {
    getSettingListSize,
    getSettingMetricsTimespan,
    getSettingPackageInfoPreference,
    getSettingTheme,
    saveSettingListSize,
    saveSettingPackageInfoPreference,
    saveSettingTheme,
    saveSettingsMetricsTimespan,
} from "./functions";

const UserSettings = () => {
    const [, setTheme] = useTheme();

    function setLightTheme() {
        setTheme("light");
        localStorage.setItem("theme", "light");
        saveSettingTheme("light");
    }

    function setDarkTheme() {
        setTheme("dark");
        localStorage.setItem("theme", "dark");
        saveSettingTheme("dark");
    }

    return (
        <Card sx={{ marginTop: 2 }}>
            <Title title="Settings" />
            <CardHeader title="Settings" />
            <CardContent>
                <Stack sx={{ width: "100%" }}>
                    <Typography variant="subtitle1">Theme</Typography>
                    <FormControl>
                        <RadioGroup defaultValue={getSettingTheme()} name="radio-buttons-group-theme" row>
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
                        </RadioGroup>
                    </FormControl>

                    <Typography variant="subtitle1" sx={{ marginTop: 2 }}>
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

                    <Typography variant="subtitle1" sx={{ marginTop: 2 }}>
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

                    <Typography variant="subtitle1" sx={{ marginTop: 2 }}>
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
                </Stack>
            </CardContent>
        </Card>
    );
};

export default UserSettings;
