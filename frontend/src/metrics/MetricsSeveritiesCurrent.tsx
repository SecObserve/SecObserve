import { Paper } from "@mui/material";
import { ArcElement, Chart as ChartJS, Legend, RadialLinearScale, Title, Tooltip } from "chart.js";
import { useEffect, useState } from "react";
import { Identifier, useNotify } from "react-admin";
import { PolarArea } from "react-chartjs-2";

import { get_severity_color } from "../commons/functions";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import {
    OBSERVATION_SEVERITY_CRITICAL,
    OBSERVATION_SEVERITY_HIGH,
    OBSERVATION_SEVERITY_LOW,
    OBSERVATION_SEVERITY_MEDIUM,
    OBSERVATION_SEVERITY_NONE,
    OBSERVATION_SEVERITY_UNKNOWN,
} from "../core/types";
import { getBackgroundColor, getElevation, getFontColor, getGridColor } from "./functions";

interface MetricsSeveritiesCurrentProps {
    product_id: Identifier | undefined;
    on_dashboard?: boolean;
}

const MetricsSeveritiesCurrent = (props: MetricsSeveritiesCurrentProps) => {
    const [data, setData] = useState<number[]>([]);
    const [loading, setLoading] = useState(false);
    const notify = useNotify();

    const chart_data = {
        labels: [
            OBSERVATION_SEVERITY_CRITICAL,
            OBSERVATION_SEVERITY_HIGH,
            OBSERVATION_SEVERITY_MEDIUM,
            OBSERVATION_SEVERITY_LOW,
            OBSERVATION_SEVERITY_NONE,
            OBSERVATION_SEVERITY_UNKNOWN,
        ],
        datasets: [
            {
                label: "Severities of active observations",
                data: data,
                backgroundColor: [
                    get_severity_color(OBSERVATION_SEVERITY_CRITICAL),
                    get_severity_color(OBSERVATION_SEVERITY_HIGH),
                    get_severity_color(OBSERVATION_SEVERITY_MEDIUM),
                    get_severity_color(OBSERVATION_SEVERITY_LOW),
                    get_severity_color(OBSERVATION_SEVERITY_NONE),
                    get_severity_color(OBSERVATION_SEVERITY_UNKNOWN),
                ],
            },
        ],
    };

    useEffect(() => {
        get_data();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function get_data() {
        setLoading(true);

        let url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/metrics/product_metrics_current/";
        if (props.product_id) {
            url += "?product_id=" + props.product_id;
        }

        httpClient(url, {
            method: "GET",
        })
            .then((result) => {
                const new_data = [
                    result.json.active_critical,
                    result.json.active_high,
                    result.json.active_medium,
                    result.json.active_low,
                    result.json.active_none,
                    result.json.active_unknown,
                ];
                setData((data) => data.concat(new_data));
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

    ChartJS.register(Title, Legend, RadialLinearScale, ArcElement, Tooltip);

    return (
        <Paper
            elevation={getElevation(props.on_dashboard)}
            sx={{
                alignItems: "center",
                display: "flex",
                justifyContent: "flex-center",
                width: "33%",
            }}
        >
            {!loading && (
                <PolarArea
                    data={chart_data}
                    options={{
                        borderColor: getBackgroundColor(),
                        scales: {
                            r: {
                                display: true,
                                grid: {
                                    circular: true,
                                    color: getGridColor(),
                                },
                                min: 0,
                                suggestedMax: 5,
                                ticks: {
                                    precision: 0,
                                    backdropColor: getBackgroundColor(),
                                    color: getFontColor(),
                                },
                            },
                            rAxes: {
                                display: false,
                            },
                        },
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: "Severities of active observations (current)",
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

export default MetricsSeveritiesCurrent;
