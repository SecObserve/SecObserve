import { Stack } from "@mui/material";
import { useEffect, useState } from "react";
import {
    BooleanField,
    ChipField,
    Datagrid,
    FunctionField,
    Identifier,
    ListContextProvider,
    NumberField,
    ResourceContextProvider,
    TextField,
    WithListContext,
    useListController,
} from "react-admin";

import { PERMISSION_OBSERVATION_ASSESSMENT, PERMISSION_OBSERVATION_DELETE } from "../../access_control/types";
import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { has_attribute, humanReadableDate } from "../../commons/functions";
import { usePublishBranchFilter } from "../products/BranchFilterContext";
import { usePublishFilterValues } from "../products/FilterValuesContext";
import { OBSERVATION_STATUS_ACTIVE, Observation } from "../types";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import ObservationBulkDeleteButton from "./ObservationBulkDeleteButton";
import ObservationExpand from "./ObservationExpand";
import { ObservationFilterBar } from "./ObservationFilterBar";
import { IDENTIFIER_OBSERVATION_EMBEDDED_LIST, setListIdentifier } from "./functions";

const ShowObservations = (id: any) => {
    return "../../../../observations/" + id + "/show";
};

type ObservationsEmbeddedListProps = {
    product: any;
};

const BulkActionButtons = (product: any) => (
    <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
        {product.product?.permissions?.includes(PERMISSION_OBSERVATION_ASSESSMENT) && (
            <ObservationBulkAssessment product={product.product} storeKey="observations.embedded" />
        )}
        {product.product?.permissions?.includes(PERMISSION_OBSERVATION_DELETE) && (
            <ObservationBulkDeleteButton product={product.product} storeKey="observations.embedded" />
        )}
    </Stack>
);

// The list must not be rendered before the product change has been processed:
// the stored list params have to be removed before useListController is mounted,
// otherwise it reads the params of the previous product instead of the filterDefaultValues.
const ObservationsEmbeddedList = ({ product }: ObservationsEmbeddedListProps) => {
    setListIdentifier(IDENTIFIER_OBSERVATION_EMBEDDED_LIST);

    const [initializedProductId, setInitializedProductId] = useState<Identifier | null>(null);

    useEffect(() => {
        const current_product_id = localStorage.getItem("observationembeddedlist.product");
        if (current_product_id == null || Number(current_product_id) !== Number(product.id)) {
            localStorage.removeItem("RaStore.observations.embedded");
            localStorage.removeItem("RaStore.license_components.embedded");
            localStorage.removeItem("RaStore.license_components.overview");
            localStorage.removeItem("RaStore.vulnerability_checks.embedded");
            localStorage.setItem("observationembeddedlist.product", String(product.id));
        }
        setInitializedProductId(product.id);
    }, [product.id]);

    if (initializedProductId !== product.id) {
        return <div>Loading...</div>;
    }

    return <ObservationsListContent product={product} />;
};

const ObservationsListContent = ({ product }: ObservationsEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: getSettingRowsPerPage(),
        resource: "observations",
        sort: { field: "current_severity", order: "ASC" },
        filterDefaultValues: {
            current_status: OBSERVATION_STATUS_ACTIVE,
            ...(product.repository_default_branch ? { branch: product.repository_default_branch } : {}),
        },
        disableSyncWithLocation: false,
        storeKey: "observations.embedded",
    });

    usePublishBranchFilter("observations", listContext.filterValues?.branch);
    usePublishFilterValues(listContext.filterValues, listContext.sort);

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="observations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <ObservationFilterBar product={product} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                sx={{ width: "100%" }}
                                rowClick={ShowObservations}
                                bulkActionButtons={
                                    product &&
                                    (product?.permissions?.includes(PERMISSION_OBSERVATION_ASSESSMENT) ||
                                        product?.permissions?.includes(PERMISSION_OBSERVATION_DELETE)) && (
                                        <BulkActionButtons product={product} />
                                    )
                                }
                                resource="observations"
                                expand={<ObservationExpand showComponent={true} />}
                                expandSingle
                            >
                                {has_attribute("branch_name", data, sort) && (
                                    <TextField source="branch_name" label="Branch / Version" />
                                )}
                                <TextField source="title" />
                                <SeverityField label="Severity" source="current_severity" />
                                <ChipField source="current_status" label="Status" />
                                {has_attribute("current_priority", data, sort) && (
                                    <ChipField source="current_priority" label="Priority" />
                                )}
                                {has_attribute("epss_score", data, sort) && (
                                    <NumberField source="epss_score" label="EPSS" />
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
                                    <TextField
                                        source="origin_endpoint_hostname"
                                        label="Host"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("origin_source_file_short", data, sort) && (
                                    <TextField
                                        source="origin_source_file_short"
                                        label="Source"
                                        sx={{ wordBreak: "break-word" }}
                                    />
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
                                {product?.has_potential_duplicates && (
                                    <BooleanField source="has_potential_duplicates" label="Dupl." textAlign="center" />
                                )}
                                {has_attribute("update_impact_score", data, sort) && (
                                    <TextField source="update_impact_score" label="Update impact score" />
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

export default ObservationsEmbeddedList;
