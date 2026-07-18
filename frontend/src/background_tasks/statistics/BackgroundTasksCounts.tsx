import { Paper, Stack, Typography } from "@mui/material";

import { getElevation } from "../../metrics/functions";
import { BackgroundTaskCounts } from "../types";

interface BackgroundTasksCountsProps {
    counts: BackgroundTaskCounts;
}

const COUNT_ITEMS: { label: string; value: (counts: BackgroundTaskCounts) => number }[] = [
    { label: "Queued", value: (counts) => Math.max(0, counts.enqueued - counts.executing) },
    { label: "Executing", value: (counts) => Math.max(0, counts.executing - counts.complete - counts.error) },
    { label: "Completed (24h)", value: (counts) => counts.complete },
    { label: "Errors (24h)", value: (counts) => counts.error },
];

const BackgroundTasksCounts = (props: BackgroundTasksCountsProps) => {
    return (
        <Stack direction="row" spacing={2}>
            {COUNT_ITEMS.map((item) => (
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
                    <Typography variant="h4">{item.value(props.counts)}</Typography>
                    <Typography variant="body2" sx={{ marginTop: 1 }}>
                        {item.label}
                    </Typography>
                </Paper>
            ))}
        </Stack>
    );
};

export default BackgroundTasksCounts;
