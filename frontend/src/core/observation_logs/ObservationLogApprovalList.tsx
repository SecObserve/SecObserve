import { Stack } from "@mui/material";
import { Fragment } from "react";
import {
    AutocompleteInput,
    ChipField,
    Datagrid,
    DateField,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { PERMISSION_OBSERVATION_LOG_APPROVAL } from "../../access_control/types";
import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ObservationLogPriorityField } from "../../commons/custom_fields/ObservationLogPriorityField";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { feature_vex_enabled, getUserOptionText, has_attribute } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { ASSESSMENT_STATUS_NEEDS_APPROVAL, OBSERVATION_SEVERITY_CHOICES, OBSERVATION_STATUS_CHOICES } from "../types";
import AssessmentBulkApproval from "./AssessmentBulkApproval";
import AssessmentDeleteApproval from "./AssessmentDeleteApproval";
import { commentShortened } from "./functions";

type BulkActionButtonsProps = {
    product: any;
    storeKey: string;
};

const BulkActionButtons = ({ product, storeKey }: BulkActionButtonsProps) => {
    return (
        <Fragment>
            {(!product || product?.permissions?.includes(PERMISSION_OBSERVATION_LOG_APPROVAL)) && (
                <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
                    <AssessmentBulkApproval storeKey={storeKey} />
                    <AssessmentDeleteApproval storeKey={storeKey} />
                </Stack>
            )}
        </Fragment>
    );
};

function listFilters(product: any, is_product_group: boolean) {
    const filters = [];

    filters.push(<TextInput source="observation_title" label="Observation title" alwaysOn />);

    if (!product) {
        filters.push(
            <ProductReferenceInput alwaysOn />,
            <ProductGroupReferenceInput alwaysOn />,
            <TextInput source="branch_name" label="Branch / Version" alwaysOn />,
            <TextInput source="origin_service_name" label="Service" alwaysOn />
        );
    } else if (is_product_group) {
        filters.push(
            <ProductReferenceInput alwaysOn />,
            <TextInput source="branch_name" label="Branch / Version" alwaysOn />,
            <TextInput source="origin_service_name" label="Service" alwaysOn />
        );
    }

    if (product?.has_branches) {
        filters.push(<BranchReferenceInput source="branch" product={product.id} alwaysOn />);
    }
    if (product?.has_services) {
        filters.push(<ServiceReferenceInput source="origin_service" product={product.id} alwaysOn />);
    }

    if (!product || product?.has_component) {
        filters.push(<TextInput source="origin_component_name_version" label="Component" alwaysOn />);
    }
    if (!product || product?.has_docker_image) {
        filters.push(<TextInput source="origin_docker_image_name_tag_short" label="Container" alwaysOn />);
    }
    if (!product || product?.has_endpoint) {
        filters.push(<TextInput source="origin_endpoint_hostname" label="Host" alwaysOn />);
    }
    if (!product || product?.has_source) {
        filters.push(<TextInput source="origin_source_file" label="Source" alwaysOn />);
    }
    if (!product || product?.has_cloud_resource) {
        filters.push(<TextInput source="origin_cloud_qualified_resource" label="Cloud resource" alwaysOn />);
    }
    if (!product || product?.has_kubernetes_resource) {
        filters.push(<TextInput source="origin_kubernetes_qualified_resource" label="Kubernetes resource" alwaysOn />);
    }

    filters.push(
        <ReferenceInput source="user" reference="users" sort={{ field: "full_name", order: "ASC" }} alwaysOn>
            <AutocompleteInputMedium optionText={getUserOptionText} />
        </ReferenceInput>,
        <AutocompleteInput source="severity" label="Severity" choices={OBSERVATION_SEVERITY_CHOICES} alwaysOn />,
        <AutocompleteInput source="status" label="Status" choices={OBSERVATION_STATUS_CHOICES} alwaysOn />
    );
    return filters;
}

type ObservationLogApprovalListProps = {
    product?: any;
    is_product_group?: boolean;
};

const ObservationLogApprovalList = ({ product, is_product_group = false }: ObservationLogApprovalListProps) => {
    let filter: Record<string, any> = { assessment_status: ASSESSMENT_STATUS_NEEDS_APPROVAL };
    if (product) {
        filter = is_product_group
            ? { ...filter, product_group: Number(product.id) }
            : { ...filter, product: Number(product.id) };
    }
    let storeKey = "observation_logs.approval";
    if (product) {
        storeKey = is_product_group ? "observation_logs.approvalproductgroup" : "observation_logs.approvalproduct";
    }
    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: "observation_logs",
        sort: { field: "created", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: storeKey,
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    const ShowObservationLogs = (id: any) => {
        return "../../../../observation_logs/" + id + "/show";
    };

    if (product && is_product_group) {
        localStorage.setItem("observationlogapprovallistproductgroup", "true");
        localStorage.removeItem("observationlogapprovallistproduct");
        localStorage.removeItem("observationlogapprovallist");
    } else if (product) {
        localStorage.setItem("observationlogapprovallistproduct", "true");
        localStorage.removeItem("observationlogapprovallist");
        localStorage.removeItem("observationlogapprovallistproductgroup");
    } else {
        localStorage.setItem("observationlogapprovallist", "true");
        localStorage.removeItem("observationlogapprovallistproduct");
        localStorage.removeItem("observationlogapprovallistproductgroup");
    }
    localStorage.removeItem("observationlogembeddedlist");

    return (
        <ResourceContextProvider value="observation_logs">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters(product, is_product_group)} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                sx={{ width: "100%" }}
                                bulkActionButtons={
                                    !product || product?.permissions?.includes(PERMISSION_OBSERVATION_LOG_APPROVAL) ? (
                                        <BulkActionButtons product={product} storeKey={storeKey} />
                                    ) : (
                                        false
                                    )
                                }
                                rowClick={ShowObservationLogs}
                                resource="observation_logs"
                            >
                                <TextField source="observation_data.title" label="Observation" />
                                {(!product || is_product_group) && (
                                    <TextField source="observation_data.product_data.name" label="Product" />
                                )}
                                {!product &&
                                    has_attribute("observation_data.product_data.product_group_name", data, sort) && (
                                        <TextField
                                            source="observation_data.product_data.product_group_name"
                                            label="Group"
                                        />
                                    )}
                                {has_attribute("observation_data.branch_name", data, sort) && (
                                    <TextField source="observation_data.branch_name" label="Branch / Version" />
                                )}
                                {has_attribute("observation_data.origin_service_name", data, sort) && (
                                    <TextField source="observation_data.origin_service_name" label="Service" />
                                )}
                                {has_attribute("observation_data.origin_component_name_version", data, sort) && (
                                    <TextField
                                        source="observation_data.origin_component_name_version"
                                        label="Component"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("observation_data.origin_docker_image_name_tag_short", data, sort) && (
                                    <TextField
                                        source="observation_data.origin_docker_image_name_tag_short"
                                        label="Container"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("observation_data.origin_endpoint_hostname", data, sort) && (
                                    <TextField
                                        source="observation_data.origin_endpoint_hostname"
                                        label="Host"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("observation_data.origin_source_file", data, sort) && (
                                    <TextField
                                        source="observation_data.origin_source_file"
                                        label="Source"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("observation_data.origin_cloud_qualified_resource", data, sort) && (
                                    <TextField
                                        source="observation_data.origin_cloud_qualified_resource"
                                        label="Cloud res."
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("observation_data.origin_kubernetes_qualified_resource", data, sort) && (
                                    <TextField
                                        source="observation_data.origin_kubernetes_qualified_resource"
                                        label="Kube. res."
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                <TextField source="user_full_name" label="User" />
                                <SeverityField label="Severity" source="severity" />
                                <ChipField source="status" label="Status" emptyText="---" />
                                {data?.some((element: any) => element.priority_changed) && (
                                    <ObservationLogPriorityField source="priority" sortable={false} />
                                )}
                                {feature_vex_enabled() && has_attribute("vex_justification", data, sort) && (
                                    <TextField
                                        label="VEX justification"
                                        source="vex_justification"
                                        emptyText="---"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                <FunctionField
                                    label="Comment"
                                    render={(record) => commentShortened(record.comment)}
                                    sortable={false}
                                    sx={{ wordBreak: "break-word" }}
                                />
                                <DateField source="created" showTime />
                            </Datagrid>
                        )}
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ObservationLogApprovalList;
