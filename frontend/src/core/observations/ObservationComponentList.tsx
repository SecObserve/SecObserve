import {
    AutocompleteArrayInput,
    ChipField,
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { SeverityField } from "../../commons/custom_fields/SeverityField";
import { has_attribute, humanReadableDate } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import {
    AGE_CHOICES,
    OBSERVATION_SEVERITY_CHOICES,
    OBSERVATION_STATUS_ACTIVE,
    OBSERVATION_STATUS_CHOICES,
    Observation,
} from "../types";
import ObservationExpand from "./ObservationExpand";
import { IDENTIFIER_OBSERVATION_COMPONENT_LIST, setListIdentifier } from "./functions";

function listFilters() {
    const filters = [];
    filters.push(
        <TextInput source="title" alwaysOn />,
        <AutocompleteArrayInput
            source="current_severity"
            label="Severity"
            choices={OBSERVATION_SEVERITY_CHOICES}
            alwaysOn
        />,
        <AutocompleteArrayInput source="current_status" label="Status" choices={OBSERVATION_STATUS_CHOICES} alwaysOn />,
        <ProductReferenceInput alwaysOn />,
        <ProductGroupReferenceInput alwaysOn />,
        <TextInput source="branch_name" label="Branch / Version" alwaysOn />,
        <TextInput source="origin_service_name" label="Service" alwaysOn />,
        <TextInput source="scanner" alwaysOn />,
        <AutocompleteInputMedium source="age" choices={AGE_CHOICES} alwaysOn />
    );

    return filters;
}

const ShowObservations = (id: any) => {
    return "../../../../observations/" + id + "/show";
};

type ObservationsComponentListProps = {
    component: any;
};

const ObservationsComponentList = ({ component }: ObservationsComponentListProps) => {
    setListIdentifier(IDENTIFIER_OBSERVATION_COMPONENT_LIST);

    const listContext = useListController({
        filter: {
            origin_component: component.id,
        },
        perPage: getSettingRowsPerPage(),
        resource: "observations",
        sort: { field: "current_severity", order: "ASC" },
        filterDefaultValues: { current_status: OBSERVATION_STATUS_ACTIVE },
        disableSyncWithLocation: false,
        storeKey: "observations.component",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="observations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                sx={{ width: "100%" }}
                                rowClick={ShowObservations}
                                resource="observations"
                                expand={<ObservationExpand showComponent={false} />}
                                expandSingle
                                bulkActionButtons={false}
                            >
                                <TextField source="title" />
                                <SeverityField label="Severity" source="current_severity" />
                                <ChipField source="current_status" label="Status" />
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

export default ObservationsComponentList;
