import {
    ChipField,
    Datagrid,
    FilterForm,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    TextInput,
    WithListContext,
    useListController,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { has_attribute } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import { VEX_STATUS_CHOICES } from "../types";

const ShowVEXStatement = (id: any) => {
    return "../../../../vex/vex_statements/" + id + "/show";
};

function listFilters() {
    return [
        <TextInput source="vulnerability_id" label="Vulnerability ID" alwaysOn />,
        <AutocompleteInputMedium source="status" choices={VEX_STATUS_CHOICES} alwaysOn />,
    ];
}

type VEXStatementEmbeddedListProps = {
    vex_document: any;
};

const VEXStatementEmbeddedList = ({ vex_document }: VEXStatementEmbeddedListProps) => {
    const listContext = useListController({
        filter: { document: Number(vex_document.id) },
        perPage: 25,
        resource: "vex/vex_statements",
        sort: { field: "vulnerability_id", order: "ASC" },
        disableSyncWithLocation: false,
        storeKey: "vex_statements.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="vex_statements">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <FilterForm filters={listFilters()} />
                    <WithListContext
                        render={({ data, sort }) => (
                            <Datagrid
                                size={getSettingListSize()}
                                rowClick={ShowVEXStatement}
                                bulkActionButtons={false}
                                resource="vex/vex_statements"
                            >
                                <TextField source="vulnerability_id" label="Vulnerability ID" />
                                <ChipField source="status" />
                                {has_attribute("product_purl", data, sort) && (
                                    <TextField source="product_purl" label="Product" />
                                )}
                                {has_attribute("component_purl", data, sort) && (
                                    <TextField source="component_purl" label="Component" />
                                )}
                                {has_attribute("component_cyclonedx_bom_link", data, sort) && (
                                    <TextField source="component_cyclonedx_bom_link" label="CycloneDX BOM Link" />
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

export default VEXStatementEmbeddedList;
