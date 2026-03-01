import { Paper } from "@mui/material";
import { ArcElement, Chart as ChartJS, Legend, RadialLinearScale, Title, Tooltip } from "chart.js";
import { useEffect, useState } from "react";
import { Identifier, useNotify } from "react-admin";
import { PolarArea } from "react-chartjs-2";

import { httpClient } from "../commons/ra-data-django-rest-framework";
import {
    OBSERVATION_STATUS_AFFECTED,
    OBSERVATION_STATUS_DUPLICATE,
    OBSERVATION_STATUS_FALSE_POSITIVE,
    OBSERVATION_STATUS_IN_REVIEW,
    OBSERVATION_STATUS_NOT_AFFECTED,
    OBSERVATION_STATUS_NOT_SECURITY,
    OBSERVATION_STATUS_OPEN,
    OBSERVATION_STATUS_RESOLVED,
    OBSERVATION_STATUS_RISK_ACCEPTED,
} from "../core/types";
import { getBackgroundColor, getElevation, getFontColor, getGridColor } from "./functions";

interface MetricsStatusCurrentProps {
    product_id: Identifier | undefined;
    on_dashboard?: boolean;
}

const MetricsStatusCurrent = (props: MetricsStatusCurrentProps) => {
    const [data, setData] = useState<number[]>([]);
    const [loading, setLoading] = useState(false);
    const notify = useNotify();

    const chart_data = {
        labels: [
            OBSERVATION_STATUS_OPEN,
            OBSERVATION_STATUS_AFFECTED,
            OBSERVATION_STATUS_IN_REVIEW,
            OBSERVATION_STATUS_RESOLVED,
            OBSERVATION_STATUS_DUPLICATE,
            OBSERVATION_STATUS_FALSE_POSITIVE,
            OBSERVATION_STATUS_NOT_AFFECTED,
            OBSERVATION_STATUS_NOT_SECURITY,
            OBSERVATION_STATUS_RISK_ACCEPTED,
        ],
        datasets: [
            {
                label: "Status of observations",
                data: data,
                backgroundColor: [
                    "#642915",
                    "#963e20",
                    "#c7522a",
                    "#e5c185",
                    "#fbf2c4",
                    "#74a892",
                    "#008585",
                    "#006464",
                    "#004343",
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
                    result.json.open,
                    result.json.affected,
                    result.json.in_review,
                    result.json.resolved,
                    result.json.duplicate,
                    result.json.false_positive,
                    result.json.not_affected,
                    result.json.not_security,
                    result.json.risk_accepted,
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
                                text: "Status of observations (current)",
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

export default MetricsStatusCurrent;
