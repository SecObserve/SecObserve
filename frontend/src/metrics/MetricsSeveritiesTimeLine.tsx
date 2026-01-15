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

interface MetricsSeveritiesTimelineProps {
    product_id: Identifier | undefined;
    on_dashboard?: boolean;
}

const MetricsSeveritiesTimeline = (props: MetricsSeveritiesTimelineProps) => {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const notify = useNotify();

    const days = [];
    for (let i = getSettingsMetricsTimespanInDays() - 1; i >= 0; i--) {
        days.push(new Date(Date.now() - i * 24 * 60 * 60 * 1000).toLocaleDateString());
    }

    function get_metrics(date: Date, metrics_data: any) {
        const date_string = date.toISOString().split("T")[0];
        const metrics = metrics_data[date_string]; // eslint-disable-line security/detect-object-injection
        if (metrics) {
            return metrics;
        } else {
            return {
                open_critical: 0,
                open_high: 0,
                open_medium: 0,
                open_low: 0,
                open_none: 0,
                open_unknown: 0,
            };
        }
    }

    const chart_data = {
        labels: days,
        datasets: datasets,
    };

    useEffect(() => {
        get_data();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function get_data() {
        setLoading(true);

        let url =
            window.__RUNTIME_CONFIG__.API_BASE_URL +
            "/metrics/product_metrics_timeline/?age=Past%20" +
            getSettingsMetricsTimespanInDays() +
            "%20days";
        if (props.product_id) {
            url += "&product_id=" + props.product_id;
        }

        httpClient(url, {
            method: "GET",
        })
            .then((result) => {
                const critical_observations = [];
                const high_observations = [];
                const medium_observations = [];
                const low_observations = [];
                const none_observations = [];
                const unknown_observations = [];

                let metrics = null;
                for (let i = getSettingsMetricsTimespanInDays() - 1; i >= 0; i--) {
                    metrics = get_metrics(new Date(Date.now() - i * 24 * 60 * 60 * 1000), result.json);
                    critical_observations.push(metrics.open_critical);
                    high_observations.push(metrics.open_high);
                    medium_observations.push(metrics.open_medium);
                    low_observations.push(metrics.open_low);
                    none_observations.push(metrics.open_none);
                    unknown_observations.push(metrics.open_unknown);
                }

                console.log(critical_observations);
                console.log(high_observations);
                console.log(medium_observations);
                console.log(low_observations);
                console.log(none_observations);
                console.log(unknown_observations);

                const data_sets = [
                    {
                        fill: true,
                        label: OBSERVATION_SEVERITY_UNKNOWN,
                        data: unknown_observations,
                        borderColor: getBackgroundColor(),
                        backgroundColor: get_severity_color(OBSERVATION_SEVERITY_UNKNOWN),
                        cubicInterpolationMode: "monotone",
                    },
                    {
                        fill: true,
                        label: OBSERVATION_SEVERITY_NONE,
                        data: none_observations,
                        borderColor: getBackgroundColor(),
                        backgroundColor: get_severity_color(OBSERVATION_SEVERITY_NONE),
                        cubicInterpolationMode: "monotone",
                    },
                    {
                        fill: true,
                        label: OBSERVATION_SEVERITY_LOW,
                        data: low_observations,
                        borderColor: getBackgroundColor(),
                        backgroundColor: get_severity_color(OBSERVATION_SEVERITY_LOW),
                        cubicInterpolationMode: "monotone",
                    },
                    {
                        fill: true,
                        label: OBSERVATION_SEVERITY_MEDIUM,
                        data: medium_observations,
                        borderColor: getBackgroundColor(),
                        backgroundColor: get_severity_color(OBSERVATION_SEVERITY_MEDIUM),
                        cubicInterpolationMode: "monotone",
                    },
                    {
                        fill: true,
                        label: OBSERVATION_SEVERITY_HIGH,
                        data: high_observations,
                        borderColor: getBackgroundColor(),
                        backgroundColor: get_severity_color(OBSERVATION_SEVERITY_HIGH),
                        cubicInterpolationMode: "monotone",
                    },
                    {
                        fill: true,
                        label: OBSERVATION_SEVERITY_CRITICAL,
                        data: critical_observations,
                        borderColor: getBackgroundColor(),
                        backgroundColor: get_severity_color(OBSERVATION_SEVERITY_CRITICAL),
                        cubicInterpolationMode: "monotone",
                    },
                ];
                setDatasets(data_sets);
            })
            .catch((error) => {
                if (error !== undefined) {
                    notify(error.message, {
                        type: "warning",
                    });
                } else {
                    notify("Error while loading metrics", {
                        type: "warning",
                    });
                }
            });
        setLoading(false);
    }

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
                                    "Severities of open observations (last " +
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
