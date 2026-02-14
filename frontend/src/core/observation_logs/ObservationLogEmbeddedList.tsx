import {
    ChipField,
    Datagrid,
    DateField,
    ListContextProvider,
    NumberField,
    ResourceContextProvider,
    TextField,
    WithListContext,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { has_attribute } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";

type ObservationLogEmbeddedListProps = {
    observation: any;
};

const ObservationLogEmbeddedList = ({ observation }: ObservationLogEmbeddedListProps) => {
    const listContext = useListController({
        filter: { observation: Number(observation.id) },
        perPage: 25,
        resource: "observation_logs",
        sort: { field: "created", order: "DESC" },
        disableSyncWithLocation: true,
        storeKey: "observation_logs.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    if (listContext.data) {
        listContext.data.forEach((element: any) => {
            if (element.comment.length > 255) {
                element.comment_shortened = element.comment.substring(0, 255) + "...";
            } else {
                element.comment_shortened = element.comment;
            }
        });
    }

    const ShowObservationLogs = (id: any) => {
        return "../../../../observation_logs/" + id + "/show";
    };

    localStorage.setItem("observationlogembeddedlist", "true");
    localStorage.removeItem("observationlogapprovallist");
    localStorage.removeItem("observationlogapprovallistproduct");

    return (
        <ResourceContextProvider value="observation_logs">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                sx={{ width: "100%" }}
                                bulkActionButtons={false}
                                rowClick={ShowObservationLogs}
                                resource="observation_logs"
                            >
                                {(observation.product_data.assessments_need_approval ||
                                    observation.product_data.product_group_assessments_need_approval) && (
                                    <ChipField source="assessment_status" sortable={false} />
                                )}
                                <TextField source="user_full_name" label="User" sortable={false} />
                                <TextField source="severity" emptyText="---" sortable={false} />
                                <TextField source="status" emptyText="---" sortable={false} />
                                {has_attribute("priority", data, sort) && (
                                    <NumberField source="priority" emptyText="---" sortable={false} />
                                )}
                                <TextField
                                    source="comment_shortened"
                                    sortable={false}
                                    label="Comment"
                                    sx={{ wordBreak: "break-word" }}
                                />
                                <DateField source="created" showTime sortable={false} />
                                {(observation.product_data.assessments_need_approval ||
                                    observation.product_data.product_group_assessments_need_approval) && (
                                    <TextField
                                        source="approval_user_full_name"
                                        label="Approved/rejected by"
                                        sortable={false}
                                    />
                                )}
                            </Datagrid>
                        )}
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ObservationLogEmbeddedList;
