import { Paper, Typography } from "@mui/material";
import { Datagrid, FunctionField, ListContextProvider, ResourceContextProvider, TextField, useList } from "react-admin";

import { getSettingListSize } from "../../commons/user_settings/functions";
import { getElevation } from "../../metrics/functions";
import { BackgroundTaskRunning } from "../types";
import { formatDuration } from "./functions";

interface BackgroundTasksRunningListProps {
    running: BackgroundTaskRunning[];
}

const BackgroundTasksRunningList = (props: BackgroundTasksRunningListProps) => {
    const listContext = useList({ data: props.running });

    return (
        <Paper elevation={getElevation()} sx={{ width: "50%", padding: 2 }}>
            <Typography variant="h6" sx={{ marginBottom: 1 }}>
                Currently running tasks
            </Typography>
            <ResourceContextProvider value="running_background_task">
                <ListContextProvider value={listContext}>
                    <Datagrid size={getSettingListSize()} bulkActionButtons={false} rowClick={false}>
                        <TextField source="task" label="Task" sx={{ wordBreak: "break-word" }} />
                        <FunctionField
                            label="Started"
                            render={(record) => new Date(record.started * 1000).toLocaleString()}
                        />
                        <FunctionField label="Elapsed" render={(record) => formatDuration(record.elapsed)} />
                    </Datagrid>
                </ListContextProvider>
            </ResourceContextProvider>
        </Paper>
    );
};

export default BackgroundTasksRunningList;
