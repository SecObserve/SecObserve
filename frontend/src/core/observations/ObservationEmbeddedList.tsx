import { Stack } from "@mui/material";
import { useEffect } from "react";
import {
    AutocompleteArrayInput,
    BooleanField,
    ChipField,
    Datagrid,
    FilterForm,
    FunctionField,
    Identifier,
    ListContextProvider,
    NullableBooleanInput,
    NumberField,
    NumberInput,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";
import { useLocation, useNavigate } from "react-router";

import { PERMISSION_OBSERVATION_ASSESSMENT, PERMISSION_OBSERVATION_DELETE } from "../../access_control/types";
import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { feature_exploit_information, has_attribute, humanReadableDate } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import {
    AGE_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_ACTIVE,
    OBSERVATION_STATUS_CHOICES,
    Observation,
    Product,
} from "../types";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import ObservationBulkDeleteButton from "./ObservationBulkDeleteButton";
import ObservationExpand from "./ObservationExpand";
import { IDENTIFIER_OBSERVATION_EMBEDDED_LIST, setListIdentifier } from "./functions";

function hasObservationListParams(search: string): boolean {
    const searchParams = new URLSearchParams(search);

    return (
        searchParams.has("filter") ||
        searchParams.has("displayedFilters") ||
        searchParams.has("page") ||
        searchParams.has("perPage") ||
        searchParams.has("sort") ||
        searchParams.has("order")
    );
}

function listFilters(product: Product) {
    const filters = [];
    if (product?.has_branches) {
        filters.push(<BranchReferenceInput source="branch" product={product.id} alwaysOn />);
    }
    filters.push(
        <TextInput source="title" alwaysOn />,
        <AutocompleteArrayInput
            source="current_severity"
            label="Severity"
            choices={OBSERVATION_SEVERITY_CHOICES}
            alwaysOn
        />,
        <AutocompleteArrayInput source="current_status" label="Status" choices={OBSERVATION_STATUS_CHOICES} alwaysOn />
    );
    if (product?.has_priorities) {
        filters.push(
            <NumberInput
                source="current_priority"
                label="Priority"
                step={1}
                min={1}
                max={99}
                sx={{ width: "7em" }}
                alwaysOn
            />
        );
    }
    if (product?.has_services) {
        filters.push(<ServiceReferenceInput source="origin_service" product={product.id} alwaysOn />);
    }

    if (product?.has_component) {
        filters.push(
            <TextInput source="origin_component_name_version" label="Component" alwaysOn />,
            <ReferenceInput
                source="origin_component_purl_type"
                reference="purl_types"
                filter={{ product: product.id, for_observations: true }}
                alwaysOn
            >
                <AutocompleteInputMedium optionText="name" label="Component type" />
            </ReferenceInput>
        );
    }
    if (product?.has_docker_image) {
        filters.push(<TextInput source="origin_docker_image_name_tag_short" label="Container" alwaysOn />);
    }
    if (product?.has_endpoint) {
        filters.push(<TextInput source="origin_endpoint_hostname" label="Host" alwaysOn />);
    }
    if (product?.has_source) {
        filters.push(<TextInput source="origin_source_file" label="Source" alwaysOn />);
    }
    if (product?.has_cloud_resource) {
        filters.push(<TextInput source="origin_cloud_qualified_resource" label="Cloud resource" alwaysOn />);
    }
    if (product?.has_kubernetes_resource) {
        filters.push(<TextInput source="origin_kubernetes_qualified_resource" label="Kubernetes resource" alwaysOn />);
    }

    filters.push(
        <TextInput source="scanner" alwaysOn />,
        <AutocompleteInputMedium source="age" choices={AGE_CHOICES} alwaysOn />,
        <TextInput source="upload_filename" label="Filename" />,
        <TextInput source="api_configuration_name" label="API configuration" />
    );
    if (product?.has_potential_duplicates) {
        filters.push(<NullableBooleanInput source="has_potential_duplicates" label="Duplicates" alwaysOn />);
    }
    if (product?.has_component) {
        if (feature_exploit_information()) {
            filters.push(<NullableBooleanInput source="cve_known_exploited" label="CVE exploited" alwaysOn />);
        }
        filters.push(<NullableBooleanInput source="fix_available" label="Fix available" alwaysOn />);
    }
    return filters;
}

const ShowObservations = (id: any) => {
    return "../../../../observations/" + id + "/show";
};

type ObservationsEmbeddedListProps = {
    product: any;
};

const BulkActionButtons = (product: any) => (
    <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
        {product.product.permissions.includes(PERMISSION_OBSERVATION_ASSESSMENT) && (
            <ObservationBulkAssessment product={product.product} storeKey="observations.embedded" />
        )}
        {product.product.permissions.includes(PERMISSION_OBSERVATION_DELETE) && (
            <ObservationBulkDeleteButton product={product.product} storeKey="observations.embedded" />
        )}
    </Stack>
);

const ObservationsEmbeddedList = ({ product }: ObservationsEmbeddedListProps) => {
    setListIdentifier(IDENTIFIER_OBSERVATION_EMBEDDED_LIST);

    const location = useLocation();
    const navigate = useNavigate();
    function get_observations_url(branch_id: Identifier): string {
        return `?displayedFilters=%7B%7D&filter=%7B%22current_status%22%3A["Open"%2C"Affected"%2C"In review"]%2C%22branch%22%3A${branch_id}%7D&order=ASC&sort=current_severity`;
    }
    useEffect(() => {
        const current_product_id = localStorage.getItem("observationembeddedlist.product");
        if (current_product_id == null || Number(current_product_id) !== product.id) {
            localStorage.removeItem("RaStore.observations.embedded");
            localStorage.removeItem("RaStore.license_components.embedded");
            localStorage.removeItem("RaStore.license_components.overview");
            localStorage.removeItem("RaStore.vulnerability_checks.embedded");
            localStorage.setItem("observationembeddedlist.product", product.id);
            if (product.repository_default_branch && !hasObservationListParams(location.search)) {
                navigate(get_observations_url(product.repository_default_branch), { replace: true });
            }
        }
    }, [location.search, navigate, product.id, product.repository_default_branch]);

    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: 25,
        resource: "observations",
        sort: { field: "current_severity", order: "ASC" },
        filterDefaultValues: { current_status: OBSERVATION_STATUS_ACTIVE, branch: product.repository_default_branch },
        disableSyncWithLocation: false,
        storeKey: "observations.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="observations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters(product)} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                sx={{ width: "100%" }}
                                rowClick={ShowObservations}
                                bulkActionButtons={
                                    product &&
                                    (product.permissions.includes(PERMISSION_OBSERVATION_ASSESSMENT) ||
                                        product.permissions.includes(PERMISSION_OBSERVATION_DELETE)) && (
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
                                    <BooleanField source="has_potential_duplicates" label="Dupl." />
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
