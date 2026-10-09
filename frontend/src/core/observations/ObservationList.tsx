import { ReactElement } from "react";
import {
    BooleanField,
    ChipField,
    Datagrid,
    FunctionField,
    ListBase,
    ListView,
    NumberField,
    TextField,
    WithListContext,
} from "react-admin";

import observations from ".";
import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { has_attribute, humanReadableDate } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { OBSERVATION_STATUS_ACTIVE, Observation } from "../types";
import ExportMenu from "./ExportMenu";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import ObservationExpand from "./ObservationExpand";
import { ObservationFilterBar } from "./ObservationFilterBar";
import { IDENTIFIER_OBSERVATION_LIST, setListIdentifier } from "./functions";

const BulkActionButtons = () => <ObservationBulkAssessment product={null} storeKey="observations.list" />;

type ObservationDatagridProps = {
    bulkActionButtons: ReactElement;
    hideProductGroup?: boolean;
};

export const ObservationDatagrid = ({ bulkActionButtons, hideProductGroup }: ObservationDatagridProps) => (
    <WithListContext
        render={({ data, sort }) => (
            <Datagrid
                size={getSettingListSize()}
                sx={{ width: "100%" }}
                rowClick="show"
                bulkActionButtons={bulkActionButtons}
                expand={<ObservationExpand showComponent={true} />}
                expandSingle
            >
                <TextField source="title" />
                <SeverityField label="Severity" source="current_severity" />
                <ChipField source="current_status" label="Status" />
                {has_attribute("current_priority", data, sort) && (
                    <ChipField source="current_priority" label="Priority" />
                )}
                {has_attribute("epss_score", data, sort) && <NumberField source="epss_score" label="EPSS" />}
                <TextField source="product_data.name" label="Product" />
                {!hideProductGroup && has_attribute("product_data.product_group_name", data, sort) && (
                    <TextField source="product_data.product_group_name" label="Group" />
                )}
                {has_attribute("branch_name", data, sort) && (
                    <TextField source="branch_name" label="Branch / Version" />
                )}
                {has_attribute("origin_service_name", data, sort) && (
                    <TextField source="origin_service_name" label="Service" />
                )}
                {has_attribute("origin_component_name_version", data, sort) && (
                    <TextField
                        source="origin_component_name_version"
                        label="Component"
                        sx={{ wordBreak: "break-word" }}
                    />
                )}
                {has_attribute("origin_docker_image_name_tag_short", data, sort) && (
                    <TextField
                        source="origin_docker_image_name_tag_short"
                        label="Container"
                        sx={{ wordBreak: "break-word" }}
                    />
                )}
                {has_attribute("origin_endpoint_hostname", data, sort) && (
                    <TextField source="origin_endpoint_hostname" label="Host" sx={{ wordBreak: "break-word" }} />
                )}
                {has_attribute("origin_source_file_short", data, sort) && (
                    <TextField source="origin_source_file_short" label="Source" sx={{ wordBreak: "break-word" }} />
                )}
                {has_attribute("origin_cloud_qualified_resource", data, sort) && (
                    <TextField
                        source="origin_cloud_qualified_resource"
                        label="Cloud resource"
                        sx={{ wordBreak: "break-word" }}
                    />
                )}
                {has_attribute("origin_kubernetes_qualified_resource", data, sort) && (
                    <TextField
                        source="origin_kubernetes_qualified_resource"
                        label="Kubernetes resource"
                        sx={{ wordBreak: "break-word" }}
                    />
                )}
                <TextField source="scanner_name" label="Scanner" />
                <FunctionField<Observation>
                    label="Age"
                    sortBy="last_observation_log"
                    render={(record) => (record ? humanReadableDate(record.last_observation_log) : "")}
                />
                <BooleanField source="has_potential_duplicates" label="Dupl." textAlign="center" />
                {has_attribute("update_impact_score", data, sort) && (
                    <TextField source="update_impact_score" label="Update impact score" />
                )}
            </Datagrid>
        )}
    />
);

const ObservationList = () => {
    setListIdentifier(IDENTIFIER_OBSERVATION_LIST);

    return (
        <ListBase
            perPage={getSettingRowsPerPage()}
            sort={{ field: "current_severity", order: "ASC" }}
            filterDefaultValues={{ current_status: OBSERVATION_STATUS_ACTIVE }}
            disableSyncWithLocation={false}
            storeKey="observations.list"
        >
            <ListHeader icon={observations.icon} title="Observations" actions={<ExportMenu />} />
            <ListView
                pagination={<CustomPagination />}
                filters={<ObservationFilterBar saveQuery />}
                actions={false}
                sx={{ marginTop: 1 }}
            >
                <ObservationDatagrid bulkActionButtons={<BulkActionButtons />} />
            </ListView>
        </ListBase>
    );
};

export default ObservationList;
