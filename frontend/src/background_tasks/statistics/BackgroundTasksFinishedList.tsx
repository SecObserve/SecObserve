import { Paper, Typography } from "@mui/material";
import {
    Datagrid,
    FunctionField,
    ListContextProvider,
    NumberField,
    ResourceContextProvider,
    TextField,
    useList,
} from "react-admin";

import { getSettingListSize } from "../../commons/user_settings/functions";
import { getElevation } from "../../metrics/functions";
import { BackgroundTaskBreakdown } from "../types";
import { formatDuration } from "./functions";

interface BackgroundTasksFinishedListProps {
    breakdown: BackgroundTaskBreakdown[];
}

const BackgroundTasksFinishedList = (props: BackgroundTasksFinishedListProps) => {
    const data = props.breakdown.map((task) => ({ ...task, id: task.full }));
    const listContext = useList({ data });

    return (
        <Paper elevation={getElevation()} sx={{ width: "50%", padding: 2 }}>
            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Finished tasks
            </Typography>
            <ResourceContextProvider value="finished_background_task">
                <ListContextProvider value={listContext}>
                    <Datagrid size={getSettingListSize()} bulkActionButtons={false} rowClick={false}>
                        <TextField source="task" label="Task" sx={{ wordBreak: "break-word" }} />
                        <NumberField source="executed" label="Executed" />
                        <NumberField source="completed" label="Completed" />
                        <NumberField source="errors" label="Errors" />
                        <FunctionField
                            label="Average"
                            render={(record) => (record.avg != null ? formatDuration(record.avg) : "-")}
                        />
                    </Datagrid>
                </ListContextProvider>
            </ResourceContextProvider>
        </Paper>
    );
};

export default BackgroundTasksFinishedList;
