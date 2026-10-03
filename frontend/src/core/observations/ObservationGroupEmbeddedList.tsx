import { useEffect, useState } from "react";
import {
    AutocompleteArrayInput,
    ChipField,
    Datagrid,
    FilterForm,
    FunctionField,
    Identifier,
    ListContextProvider,
    NullableBooleanInput,
    ReferenceInput,
    ResourceContextProvider,
    SelectInput,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { feature_exploit_information, has_attribute, humanReadableDate } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { usePublishFilterValues } from "../products/FilterValuesContext";
import {
    AGE_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_ACTIVE,
    OBSERVATION_STATUS_CHOICES,
    Observation,
    ProductGroup,
} from "../types";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import ObservationExpand from "./ObservationExpand";
import { IDENTIFIER_OBSERVATION_GROUP_EMBEDDED_LIST, setListIdentifier } from "./functions";

const STORE_KEY = "observations.embedded.group";

function listFilters(product_group: ProductGroup) {
    const filters = [
        <SelectInput
            source="default_branch"
            label="Branches"
            choices={[{ id: true, name: "Default branches" }]}
            emptyText="All branches"
            // Shows "All branches" instead of an empty field when the filter is removed
            slotProps={{ select: { displayEmpty: true }, inputLabel: { shrink: true } }}
            alwaysOn
        />,
        <ReferenceInput
            source="product"
            reference="products"
            filter={{ product_group: product_group.id }}
            queryOptions={{ meta: { api_resource: "product_names" } }}
            sort={{ field: "name", order: "ASC" }}
            alwaysOn
        >
            <AutocompleteInputMedium optionText="name" />
        </ReferenceInput>,
        <TextInput source="title" alwaysOn />,
        <AutocompleteArrayInput
            source="current_severity"
            label="Severity"
            choices={OBSERVATION_SEVERITY_CHOICES}
            alwaysOn
        />,
        <AutocompleteArrayInput source="current_status" label="Status" choices={OBSERVATION_STATUS_CHOICES} alwaysOn />,
        <TextInput source="branch_name" label="Branch / Version" alwaysOn />,
        <TextInput source="origin_component_name_version" label="Component" alwaysOn />,
        <TextInput source="scanner" alwaysOn />,
        <AutocompleteInputMedium source="age" choices={AGE_CHOICES} alwaysOn />,
    ];
    if (feature_exploit_information()) {
        filters.push(<NullableBooleanInput source="cve_known_exploited" label="CVE exploited" alwaysOn />);
    }
    filters.push(<NullableBooleanInput source="fix_available" label="Fix available" alwaysOn />);
    return filters;
}

type ObservationGroupEmbeddedListProps = {
    product_group: ProductGroup;
};

// The stored list params of the previous product group have to be removed before useListController is mounted
const ObservationGroupEmbeddedList = ({ product_group }: ObservationGroupEmbeddedListProps) => {
    setListIdentifier(IDENTIFIER_OBSERVATION_GROUP_EMBEDDED_LIST);

    const [initializedProductGroupId, setInitializedProductGroupId] = useState<Identifier | null>(null);

    useEffect(() => {
        const current_product_group_id = localStorage.getItem("observationgroupembeddedlist.product_group");
        if (current_product_group_id == null || Number(current_product_group_id) !== Number(product_group.id)) {
            localStorage.removeItem("RaStore." + STORE_KEY);
            localStorage.setItem("observationgroupembeddedlist.product_group", String(product_group.id));
        }
        setInitializedProductGroupId(product_group.id);
    }, [product_group.id]);

    if (initializedProductGroupId !== product_group.id) {
        return <div>Loading...</div>;
    }

    return <ObservationGroupListContent product_group={product_group} />;
};

const ObservationGroupListContent = ({ product_group }: ObservationGroupEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product_group: Number(product_group.id) },
        perPage: getSettingRowsPerPage(),
        resource: "observations",
        sort: { field: "current_severity", order: "ASC" },
        filterDefaultValues: { current_status: OBSERVATION_STATUS_ACTIVE, default_branch: true },
        disableSyncWithLocation: false,
        storeKey: STORE_KEY,
    });

    usePublishFilterValues(listContext.filterValues);

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="observations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters(product_group)} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                sx={{ width: "100%" }}
                                rowClick="show"
                                bulkActionButtons={<ObservationBulkAssessment product={null} storeKey={STORE_KEY} />}
                                resource="observations"
                                expand={<ObservationExpand showComponent={true} />}
                                expandSingle
                            >
                                <TextField source="product_data.name" label="Product" />
                                {has_attribute("branch_name", data, sort) && (
                                    <TextField source="branch_name" label="Branch / Version" />
                                )}
                                <TextField source="title" />
                                <SeverityField label="Severity" source="current_severity" />
                                <ChipField source="current_status" label="Status" />
                                {has_attribute("origin_component_name_version", data, sort) && (
                                    <TextField
                                        source="origin_component_name_version"
                                        label="Component"
                                        sx={{ wordBreak: "break-word" }}
                                    />
                                )}
                                <TextField source="scanner_name" label="Scanner" />
                                <FunctionField<Observation>
                                    label="Age"
                                    sortBy="last_observation_log"
                                    render={(record) => (record ? humanReadableDate(record.last_observation_log) : "")}
                                />
                            </Datagrid>
                        )}
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ObservationGroupEmbeddedList;
