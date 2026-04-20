import { Stack } from "@mui/material";
import {
    Datagrid,
    FilterForm,
    ListContextProvider,
    ReferenceField,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithRecord,
    useListController,
} from "react-admin";

import { PERMISSION_API_CONFIGURATION_DELETE, PERMISSION_API_CONFIGURATION_EDIT } from "../../access_control/types";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import APIConfigurationDelete from "./ApiConfigurationDelete";
import ApiConfigurationEdit from "./ApiConfigurationEdit";

const listFilters = [
    <TextInput source="name" alwaysOn />,
    <ReferenceInput
        source="parser"
        reference="parsers"
        filter={{ source: "API" }}
        sort={{ field: "name", order: "ASC" }}
        alwaysOn
    >
        <AutocompleteInputMedium optionText="name" />
    </ReferenceInput>,
];

type ApiConfigurationEmbeddedListProps = {
    product: any;
};

const ApiConfigurationEmbeddedList = ({ product }: ApiConfigurationEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: getSettingRowsPerPage(),
        resource: "api_configurations",
        sort: { field: "name", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: "api_configurations.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="api_configurations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters} />
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                    >
                        <TextField source="name" />
                        <ReferenceField
                            source="parser"
                            reference="parsers"
                            link={false}
                            sx={{ "& a": { textDecoration: "none" } }}
                        />
                        <TextField source="base_url" label="Base URL" />
                        <TextField source="query" label="Query" />
                        <TextField source="project_key" />
                        <WithRecord
                            render={(api_configuration) => (
                                <Stack direction="row" spacing={4}>
                                    {product?.permissions.includes(PERMISSION_API_CONFIGURATION_EDIT) && (
                                        <ApiConfigurationEdit />
                                    )}
                                    {product?.permissions.includes(PERMISSION_API_CONFIGURATION_DELETE) && (
                                        <APIConfigurationDelete api_configuration={api_configuration} />
                                    )}
                                </Stack>
                            )}
                        />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ApiConfigurationEmbeddedList;
