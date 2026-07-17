import { Paper } from "@mui/material";
import {
    CategoryScale,
    Chart as ChartJS,
    Filler,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    Title,
    Tooltip,
} from "chart.js";
import { useEffect, useState } from "react";
import { Identifier, useNotify } from "react-admin";
import { Line } from "react-chartjs-2";

import { get_severity_color } from "../commons/functions";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import { getSettingsMetricsTimespanInDays } from "../commons/user_settings/functions";
import {
    OBSERVATION_SEVERITY_CRITICAL,
    OBSERVATION_SEVERITY_HIGH,
    OBSERVATION_SEVERITY_LOW,
    OBSERVATION_SEVERITY_MEDIUM,
    OBSERVATION_SEVERITY_NONE,
    OBSERVATION_SEVERITY_UNKNOWN,
} from "../core/types";
import { getBackgroundColor, getElevation, getFontColor, getGridColor } from "./functions";
import { TimeLine } from "../types";

interface BackgroundTasksTimelineProps {
    timeline: TimeLine;
}

const BackgroundTasksTimeline = (props: BackgroundTasksTimelineProps) => {
    const [datasets, setDatasets] = useState<any[]>([]);
    const notify = useNotify();

    const chart_data = {
        labels: days,
        datasets: datasets,
    };

    ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend);

    return (
        <Paper
            elevation={getElevation(props.on_dashboard)}
            sx={{
                alignItems: "top",
                display: "flex",
                justifyContent: "flex-center",
                width: "33%",
            }}
        >
            {!loading && (
                <Line
                    width="50vw"
                    height="50vw"
                    data={chart_data}
                    options={{
                        scales: {
                            y: {
                                min: 0,
                                suggestedMax: 5,
                                ticks: {
                                    precision: 0,
                                },
                                stacked: true,
                                grid: {
                                    color: getGridColor(),
                                },
                            },
                            x: {
                                grid: {
                                    color: getGridColor(),
                                },
                            },
                        },
                        borderColor: getBackgroundColor(),
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text:
                                    "Severities of active observations (last " +
                                    getSettingsMetricsTimespanInDays() +
                                    " days)",
                                color: getFontColor(),
                            },
                            legend: {
                                display: true,
                                position: "bottom",
                                labels: {
                                    color: getFontColor(),
                                },
                            },
                        },
                    }}
                />
            )}
        </Paper>
    );
};

export default MetricsSeveritiesTimeline;
