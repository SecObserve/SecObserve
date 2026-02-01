import { Stack } from "@mui/material";
import { Fragment, useEffect, useState } from "react";
import { useTheme } from "react-admin";

import { setUserInfo } from "../access_control/auth_provider/authProvider";
import { getResolvedSettingTheme, getTheme } from "../commons/user_settings/functions";
import ObservationDashboardList from "../core/observations/ObservationDashboardList";
import MetricsHeader from "../metrics/MetricsHeader";
import MetricsSeveritiesCurrent from "../metrics/MetricsSeveritiesCurrent";
import MetricsSeveritiesTimeline from "../metrics/MetricsSeveritiesTimeLine";
import MetricsStatusCurrent from "../metrics/MetricsStatusCurrent";

const Dashboard = () => {
    const [setting_theme, setSettingTheme] = useState("");
    const [, setTheme] = useTheme();

    const getUserInfo = async () => {
        const user = localStorage.getItem("user");
        if (!user) {
            await setUserInfo();
        }
        setSettingTheme(getResolvedSettingTheme());
    };

    useEffect(() => {
        getUserInfo();
        setTheme(getTheme());
    }, [setting_theme, setTheme]);

    return (
        <Fragment>
            <MetricsHeader repository_default_branch={undefined} on_dashboard={true} />
            <Stack
                direction="row"
                spacing={2}
                sx={{
                    alignItems: "top",
                    marginTop: 2,
                }}
            >
                <MetricsSeveritiesCurrent product_id={undefined} on_dashboard={true} />
                <MetricsSeveritiesTimeline product_id={undefined} on_dashboard={true} />
                <MetricsStatusCurrent product_id={undefined} on_dashboard={true} />
            </Stack>
            <ObservationDashboardList />
        </Fragment>
    );
};

export default Dashboard;
