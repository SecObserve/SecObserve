import { Stack } from "@mui/material";
import { useEffect, useState } from "react";
import { useNotify } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { BackgroundTaskStatistics } from "../types";
import BackgroundTasksCounts from "./BackgroundTasksCounts";
import BackgroundTasksFinishedList from "./BackgroundTasksFinishedList";
import BackgroundTasksRunningList from "./BackgroundTasksRunningList";
import BackgroundTasksTimeline from "./BackgroundTasksTimeLine";

const BackgroundTasksStatistics = () => {
    const [statistics, setStatistics] = useState<BackgroundTaskStatistics | null>(null);
    const notify = useNotify();

    useEffect(() => {
        get_data();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    function get_data() {
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/status/background_task_statistics/";

        httpClient(url, {
            method: "GET",
        })
            .then((result: any) => {
                setStatistics(result.json);
            })
            .catch((error: any) => {
                if (error !== undefined) {
                    notify(error.message, {
                        type: "warning",
                    });
                } else {
                    notify("Error while loading background task statistics", {
                        type: "warning",
                    });
                }
            });
    }

    return statistics ? (
        <Stack spacing={2} sx={{ marginTop: 2 }}>
            <BackgroundTasksCounts counts={statistics.counts} />
            <BackgroundTasksTimeline timeline={statistics.throughput} />
            <Stack direction="row" spacing={2} sx={{ alignItems: "flex-start" }}>
                <BackgroundTasksFinishedList breakdown={statistics.registered} />
                <BackgroundTasksRunningList running={statistics.running} />
            </Stack>
        </Stack>
    ) : null;
};

export default BackgroundTasksStatistics;
