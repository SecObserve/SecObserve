import humanizeDuration from "humanize-duration";
import {
    AutocompleteInput,
    Datagrid,
    DateField,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { PeriodicTaskStatusField } from "../../commons/custom_fields/PeriodicTaskStatusField";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { PERIODIC_TASKS_STATUS_CHOICES } from "../types";

const listFilters = [
    <TextInput key="task-filter" source="task" alwaysOn />,
    <AutocompleteInput key="status-filter" source="status" choices={PERIODIC_TASKS_STATUS_CHOICES} alwaysOn />,
];

const PeriodicTaskEmbeddedList = () => {
    const listContext = useListController({
        filter: {},
        perPage: getSettingRowsPerPage(),
        resource: "periodic_tasks",
        sort: { field: "start_time", order: "DESC" },
        disableSyncWithLocation: false,
        storeKey: "periodic_tasks.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="periodic_tasks">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters} />
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
