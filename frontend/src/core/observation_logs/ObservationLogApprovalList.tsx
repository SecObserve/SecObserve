import { Stack } from "@mui/material";
import { Fragment, ReactElement } from "react";
import {
    AutocompleteInput,
    ChipField,
    Datagrid,
    FunctionField,
    ListContextProvider,
    ReferenceInput,
    ResourceContextProvider,
    SelectField,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { PERMISSION_OBSERVATION_LOG_APPROVAL } from "../../access_control/types";
import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { AutocompleteInputAutoWidth } from "../../commons/custom_fields/AutocompleteInputAutoWidth";
import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { DateField } from "../../commons/custom_fields/DateField";
import { DateRangeFilter } from "../../commons/custom_fields/DateRangeFilter";
import { FilterBar, SecondaryFilter } from "../../commons/custom_fields/FilterBar";
import { ObservationLogPriorityField } from "../../commons/custom_fields/ObservationLogPriorityField";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { TextInputAutoWidth } from "../../commons/custom_fields/TextInputAutoWidth";
import { feature_vex_enabled, getUserOptionText, has_attribute } from "../../commons/functions";
import { originFilters } from "../observations/ObservationFilterBar";
import {
    ASSESSMENT_STATUS_NEEDS_APPROVAL,
    OBSERVATION_ALL_VEX_JUSTIFICATION_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_CHOICES,
    OBSERVATION_VEX_REMEDIATION_CATEGORY_CHOICES,
} from "../types";
import AssessmentBulkApproval from "./AssessmentBulkApproval";
import AssessmentDeleteApproval from "./AssessmentDeleteApproval";
import { ObservationLogComponent } from "./ObservationLogShow";
import ObservationLogShowAside from "./ObservationLogShowAside";
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

// The list of a product group offers the filters of the list without a product, its products are the ones of the group.
function approvalFilters(product: any, is_product_group: boolean) {
    const scoped = is_product_group ? undefined : product;
    const primary: ReactElement[] = [];

    if (scoped?.has_branches) {
        primary.push(<BranchReferenceInput source="branch" product={scoped.id} alwaysOn autoWidth />);
    }
    primary.push(<TextInputAutoWidth source="observation_title" label="Observation title" alwaysOn />);
    if (!product) {
        primary.push(
            <ProductReferenceInput key="product" alwaysOn autoWidth />,
            <ProductGroupReferenceInput key="product_group" alwaysOn autoWidth />
        );
    } else if (is_product_group) {
        primary.push(<ProductReferenceInput key="product" product_group={product.id} alwaysOn autoWidth />);
    }
    if (!scoped) {
        primary.push(<TextInputAutoWidth source="branch_name" label="Branch / Version" alwaysOn />);
    }
    primary.push(
        <ReferenceInput source="user" reference="users" sort={{ field: "full_name", order: "ASC" }} alwaysOn>
            <AutocompleteInputAutoWidth optionText={getUserOptionText} />
        </ReferenceInput>,
        <AutocompleteInput source="severity" label="Severity" choices={OBSERVATION_SEVERITY_CHOICES} alwaysOn />,
        <AutocompleteInput source="status" label="Status" choices={OBSERVATION_STATUS_CHOICES} alwaysOn />,
        <DateRangeFilter key="date" fields={[{ source: "created", label: "Created" }]} alwaysOn />
    );

    const secondary: SecondaryFilter[] = [
        ...originFilters(scoped),
        { column: "Scan", input: <TextInput source="scanner" label="Scanner" /> },
    ];

    return { primary, secondary };
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
    const { primary, secondary } = approvalFilters(product, is_product_group);
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
                    <FilterBar filters={primary} moreFilters={secondary} />
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
                                // Everything the show page has, so that several assessments can be checked before a bulk approval
                                expand={
                                    <Stack direction="row" sx={{ alignItems: "flex-start" }}>
                                        <ObservationLogComponent />
                                        <ObservationLogShowAside />
                                    </Stack>
                                }
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
                                    <SelectField
                                        label="VEX justification"
                                        source="vex_justification"
                                        choices={OBSERVATION_ALL_VEX_JUSTIFICATION_CHOICES}
                                        emptyText="---"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                {has_attribute("risk_acceptance_expiry_date", data, sort) && (
                                    <DateField
                                        source="risk_acceptance_expiry_date"
                                        label="Risk acceptance expiry"
                                        emptyText="---"
                                        sortable={false}
                                    />
                                )}
                                {feature_vex_enabled() &&
                                    data?.some((element: any) => element.vex_remediations?.length > 0) && (
                                        // Only the categories, the texts are in the expanded row
                                        <FunctionField
                                            label="VEX remediations"
                                            render={(record) =>
                                                record.vex_remediations
                                                    ?.map(
                                                        (remediation: any) =>
                                                            OBSERVATION_VEX_REMEDIATION_CATEGORY_CHOICES.find(
                                                                (choice) => choice.id === remediation.category
                                                            )?.name ?? remediation.category
                                                    )
                                                    .join(", ") || "---"
                                            }
                                            sortable={false}
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
