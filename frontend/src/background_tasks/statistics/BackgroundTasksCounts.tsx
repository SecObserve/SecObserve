import { Paper, Stack, Typography } from "@mui/material";

import { getElevation } from "../../metrics/functions";
import { BackgroundTaskCounts } from "../types";

interface BackgroundTasksCountsProps {
    counts: BackgroundTaskCounts;
    pending: number;
    running: number;
}

const BackgroundTasksCounts = (props: BackgroundTasksCountsProps) => {
    // Events can be pruned or lost, so Queued and Executing are not derived from their counts.
    const items = [
        { label: "Queued", value: props.pending },
        { label: "Executing", value: props.running },
        { label: "Completed (24h)", value: props.counts.complete },
        { label: "Errors (24h)", value: props.counts.error },
    ];

    return (
        <Stack direction="row" spacing={2}>
            {items.map((item) => (
                <Paper
                    key={item.label}
                    elevation={getElevation()}
                    sx={{
                        flex: 1,
                        padding: 2,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                    }}
                >
                    <Typography variant="h4">{item.value}</Typography>
                    <Typography variant="body2" sx={{ marginTop: 1 }}>
                        {item.label}
                    </Typography>
                </Paper>
            ))}
        </Stack>
    );
};

export default BackgroundTasksCounts;
