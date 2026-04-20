import {
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { humanReadableDate } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { AGE_CHOICES } from "../../core/types";

const showLicense = (id: any) => {
    return "../../../../concluded_licenses/" + id + "/show";
};

const listFilters = [
    <ProductReferenceInput alwaysOn />,
    <TextInput source="component_name" alwaysOn />,
    <ReferenceInput
        source="manual_concluded_spdx_license"
        reference="licenses"
        sort={{ field: "spdx_id", order: "ASC" }}
        alwaysOn
    >
        <AutocompleteInputMedium label="SPDX license" optionText="spdx_id" />
    </ReferenceInput>,
    <TextInput source="manual_concluded_license_expression" label="License expression" alwaysOn />,
    <TextInput source="manual_concluded_non_spdx_license" label="Non-SPDX license" alwaysOn />,
    <ReferenceInput source="user" reference="users" sort={{ field: "full_name", order: "ASC" }} alwaysOn>
        <AutocompleteInputMedium optionText="full_name" />
    </ReferenceInput>,
    <AutocompleteInputMedium source="age" choices={AGE_CHOICES} alwaysOn />,
];

const ConcludedLicenseEmbeddedList = () => {
    const listContext = useListController({
        filter: {},
        perPage: getSettingRowsPerPage(),
        resource: "concluded_licenses",
        sort: { field: "product_data.name", order: "ASC" },
        disableSyncWithLocation: false,
        storeKey: "concluded_licenses.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="concluded_licenses">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters} />
                    <Datagrid
                        size={getSettingListSize()}
                        rowClick={showLicense}
                        bulkActionButtons={false}
                        resource="concluded_licenses"
                    >
                        <TextField source="product_data.name" label="Product" />
                        <TextField source="component_name_version" label="Component" />
                        <TextField source="manual_concluded_spdx_license_id" label="SPDX license" />
                        <TextField source="manual_concluded_license_expression" label="License expression" />
                        <TextField source="manual_concluded_non_spdx_license" label="Non-SPDX license" />
                        <TextField source="user_data.full_name" label="User" />
                        <FunctionField<any>
                            label="Age"
                            sortBy="last_updated"
                            render={(record) => (record ? humanReadableDate(record.last_updated) : "")}
                        />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ConcludedLicenseEmbeddedList;
