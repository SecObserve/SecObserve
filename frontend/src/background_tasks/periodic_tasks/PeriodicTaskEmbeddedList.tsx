import { Stack } from "@mui/material";
import humanizeDuration from "humanize-duration";
import { useEffect, useState } from "react";
import {
    AutocompleteInput,
    Datagrid,
    DateField,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { PeriodicTaskStatusField } from "../../commons/custom_fields/PeriodicTaskStatusField";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { PERIODIC_TASKS_STATUS_CHOICES } from "../types";
import PeriodicTaskRunNow from "./PeriodicTaskRunNow";

const PeriodicTaskEmbeddedList = () => {
    const [registeredTasks, setRegisteredTasks] = useState<string[]>([]);

    const listContext = useListController({
        filter: {},
        perPage: getSettingRowsPerPage(),
        resource: "periodic_tasks",
        sort: { field: "start_time", order: "DESC" },
        disableSyncWithLocation: false,
        storeKey: "periodic_tasks.embedded",
    });

    useEffect(() => {
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/periodic_tasks/registered_tasks/", {
            method: "GET",
        }).then((registered) => {
            setRegisteredTasks(registered.json.tasks);
        });
    }, []);

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    const listFilters = [
        <AutocompleteInput
            key="task-filter"
            source="task"
            choices={registeredTasks.map((registered_task) => ({ id: registered_task, name: registered_task }))}
            alwaysOn
            sx={{ width: 480 }}
        />,
        <AutocompleteInput key="status-filter" source="status" choices={PERIODIC_TASKS_STATUS_CHOICES} alwaysOn />,
    ];

    const selected_task = registeredTasks.includes(listContext.filterValues.task)
        ? listContext.filterValues.task
        : null;

    return (
        <ResourceContextProvider value="periodic_tasks">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Stack
                        direction="row"
                        sx={{
                            alignItems: "center",
                            marginBottom: 1,
                            // shrink the filter form to its content, so that the Run now
                            // button can sit next to the filters
                            "& form": { flex: "0 1 auto", minHeight: "unset", paddingBottom: 0 },
                            "& form .RaFilterForm-filterFormInput .MuiFormControl-root": { marginTop: 0 },
                        }}
                    >
                        <FilterForm filters={listFilters} />
                        <PeriodicTaskRunNow task={selected_task} />
                    </Stack>
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={false}
                        bulkActionButtons={false}
                        resource="periodic_tasks"
                    >
                        <TextField source="task" />
                        <DateField source="start_time" showTime />
                        <FunctionField source="duration" render={(record) => `${humanizeDuration(record.duration)}`} />
                        <PeriodicTaskStatusField label="Status" />
                        <TextField source="message" sortable={false} sx={{ whiteSpace: "pre-line" }} />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default PeriodicTaskEmbeddedList;
