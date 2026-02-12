import { Fragment } from "react";
import {
    AutocompleteInput,
    BooleanField,
    ChipField,
    Datagrid,
    FilterButton,
    FunctionField,
    List,
    NullableBooleanInput,
    NumberField,
    ReferenceInput,
    TextField,
    TextInput,
    TopToolbar,
    WithListContext,
} from "react-admin";

import observations from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { feature_exploit_information, has_attribute, humanReadableDate } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium, AutocompleteInputWide } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import {
    AGE_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_CHOICES,
    OBSERVATION_STATUS_OPEN,
    Observation,
    PURL_TYPE_CHOICES,
} from "../types";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import ObservationExpand from "./ObservationExpand";
import { IDENTIFIER_OBSERVATION_LIST, setListIdentifier } from "./functions";

function listFilters() {
    const filters = [];
    filters.push(
        <TextInput source="title" alwaysOn />,
        <AutocompleteInput
            source="current_severity"
            label="Severity"
            choices={OBSERVATION_SEVERITY_CHOICES}
            alwaysOn
        />,
        <AutocompleteInput source="current_status" label="Status" choices={OBSERVATION_STATUS_CHOICES} alwaysOn />
    );
    filters.push(
        <ReferenceInput
            source="product"
            reference="products"
            sort={{ field: "name", order: "ASC" }}
            queryOptions={{ meta: { api_resource: "product_names" } }}
            alwaysOn
        >
            <AutocompleteInputMedium optionText="name" />
        </ReferenceInput>,
        <ReferenceInput
            source="product_group"
            reference="product_groups"
            sort={{ field: "name", order: "ASC" }}
            queryOptions={{ meta: { api_resource: "product_group_names" } }}
            alwaysOn
        >
            <AutocompleteInputMedium optionText="name" />
        </ReferenceInput>,
        <ReferenceInput
            source="branch"
            reference="branches"
            sort={{ field: "name", order: "ASC" }}
            queryOptions={{ meta: { api_resource: "branch_names" } }}
            alwaysOn
        >
            <AutocompleteInputWide optionText="name_with_product" label="Branch / Version" />
        </ReferenceInput>,
        <ReferenceInput
            label="Service"
            source="origin_service"
            queryOptions={{ meta: { api_resource: "service_names" } }}
            reference="services"
            sort={{ field: "name", order: "ASC" }}
        >
            <AutocompleteInputWide label="Service" optionText="name_with_product" />
        </ReferenceInput>,
        <TextInput source="origin_component_name_version" label="Component" />,
        <TextInput source="origin_docker_image_name_tag_short" label="Container" />,
        <TextInput source="origin_endpoint_hostname" label="Host" />,
        <TextInput source="origin_source_file" label="Source" />,
        <TextInput source="origin_cloud_qualified_resource" label="Cloud resource" />,
        <TextInput source="origin_kubernetes_qualified_resource" label="Kubernetes resource" />,
        <TextInput source="scanner" alwaysOn />,
        <AutocompleteInputMedium source="age" choices={AGE_CHOICES} alwaysOn />,
        <NullableBooleanInput source="has_potential_duplicates" label="Duplicates" alwaysOn />,
        <AutocompleteInput
            source="origin_component_purl_type"
            label="Component type"
            choices={PURL_TYPE_CHOICES}
            alwaysOn
        />
    );
    if (feature_exploit_information()) {
        filters.push(<NullableBooleanInput source="cve_known_exploited" label="CVE exploited" alwaysOn />);
    }
    filters.push(<NullableBooleanInput source="fix_available" label="Fix available" alwaysOn />);
    return filters;
}

const ListActions = () => (
    <TopToolbar>
        <FilterButton />
    </TopToolbar>
);

const BulkActionButtons = () => <ObservationBulkAssessment product={null} storeKey="observations.list" />;

const ObservationList = () => {
    setListIdentifier(IDENTIFIER_OBSERVATION_LIST);

    return (
        <Fragment>
            <ListHeader icon={observations.icon} title="Observations" />
            <List
                perPage={25}
                pagination={<CustomPagination />}
                filters={listFilters()}
                sort={{ field: "current_severity", order: "ASC" }}
                filterDefaultValues={{ current_status: OBSERVATION_STATUS_OPEN }}
                disableSyncWithLocation={false}
                storeKey="observations.list"
                actions={<ListActions />}
                sx={{ marginTop: 1 }}
            >
                <WithListContext
                    render={({ data, sort }) => (
                        <Datagrid
                            size={getSettingListSize()}
                            rowClick="show"
                            bulkActionButtons={<BulkActionButtons />}
                            expand={<ObservationExpand showComponent={true} />}
                            expandSingle
                        >
                            <TextField source="title" />
                            <SeverityField label="Severity" source="current_severity" />
                            <ChipField source="current_status" label="Status" />
                            {has_attribute("current_priority", data, sort) && <ChipField source="current_priority" label="Priority" />}
                            {has_attribute("epss_score", data, sort) && (
                                <NumberField source="epss_score" label="EPSS" />
                            )}
                            <TextField source="product_data.name" label="Product" />
                            {has_attribute("product_data.product_group_name", data, sort) && (
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
                                    label="Cont."
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
                                    label="Cloud res."
                                    sx={{ wordBreak: "break-word" }}
                                />
                            )}
                            {has_attribute("origin_kubernetes_qualified_resource", data, sort) && (
                                <TextField
                                    source="origin_kubernetes_qualified_resource"
                                    label="Kube. res."
                                    sx={{ wordBreak: "break-word" }}
                                />
                            )}
                            <TextField source="scanner_name" label="Scanner" />
                            <FunctionField<Observation>
                                label="Age"
                                sortBy="last_observation_log"
                                render={(record) => (record ? humanReadableDate(record.last_observation_log) : "")}
                            />
                            <BooleanField source="has_potential_duplicates" label="Dupl." />
                            {has_attribute("update_impact_score", data, sort) && (
                                <TextField source="update_impact_score" label="Update impact score" />
                            )}
                        </Datagrid>
                    )}
                />
            </List>
        </Fragment>
    );
};

export default ObservationList;
