import { Paper } from "@mui/material";
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Title, Tooltip } from "chart.js";
import { Bar } from "react-chartjs-2";

import { getBackgroundColor, getElevation, getFontColor, getGridColor } from "../../metrics/functions";
import { BackgroundTaskThroughput } from "../types";

interface BackgroundTasksTimelineProps {
    timeline: BackgroundTaskThroughput;
}

const BackgroundTasksTimeline = (props: BackgroundTasksTimelineProps) => {
    ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

    const length = props.timeline.complete.length;
    const labels = [];
    for (let i = 0; i < length; i++) {
        labels.push(
            new Date(Date.now() - (length - 1 - i) * 60 * 1000).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
            })
        );
    }

    const chart_data = {
        labels: labels,
        datasets: [
            {
                label: "Completed",
                data: props.timeline.complete,
                backgroundColor: "#53aa33",
                stack: "throughput",
            },
            {
                label: "Errors",
                data: props.timeline.error,
                backgroundColor: "#cc0500",
                stack: "throughput",
            },
        ],
    };

    return (
        <Paper
            elevation={getElevation()}
            sx={{
                width: "100%",
            }}
        >
            <Bar
                data={chart_data}
                options={{
                    maintainAspectRatio: true,
                    aspectRatio: 3,
                    scales: {
                        y: {
                            min: 0,
                            suggestedMax: 3,
                            ticks: {
                                precision: 0,
                                color: getFontColor(),
                            },
                            stacked: true,
                            grid: {
                                color: getGridColor(),
                            },
                        },
                        x: {
                            stacked: true,
                            ticks: {
                                color: getFontColor(),
                            },
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
                            text: "Background tasks throughput (last 60 minutes)",
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
        </Paper>
    );
};

export default BackgroundTasksTimeline;
