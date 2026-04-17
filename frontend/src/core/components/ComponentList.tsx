import { Fragment } from "react";
import {
    AutocompleteInput,
    BooleanField,
    Datagrid,
    List,
    NullableBooleanInput,
    TextField,
    TextInput,
    WithListContext,
} from "react-admin";

import components from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { has_attribute } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { COMPONENT_TYPE_CHOICES } from "../../licenses/types";
import { PURL_TYPE_CHOICES } from "../types";

const listFilters = [
    <TextInput source="component_name_version" label="Component" alwaysOn />,
    <AutocompleteInput source="component_purl_type" label="Ecosystem" choices={PURL_TYPE_CHOICES} alwaysOn />,
    <AutocompleteInputMedium source="component_type" label="Type" choices={COMPONENT_TYPE_CHOICES} alwaysOn />,
    <ProductReferenceInput alwaysOn />,
    <ProductGroupReferenceInput alwaysOn />,
    <TextInput source="branch_name" label="Branch / Version" alwaysOn />,
    <TextInput source="origin_service_name" label="Service" alwaysOn />,
    <NullableBooleanInput source="has_observations" label="Active observations" alwaysOn />,
];

const ComponentList = () => {
    return (
        <Fragment>
            <ListHeader icon={components.icon} title="Components" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "component_name_version_type", order: "ASC" }}
                disableSyncWithLocation={false}
                actions={false}
                storeKey="components.list"
            >
                <WithListContext
                    render={({ data, sort }) => (
                        <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={false}>
                            <TextField source="component_name_version_type" label="Component" />
                            <TextField source="component_type" label="Type" />
                            <TextField source="product_name" label="Product" />
                            {has_attribute("product_group_name", data, sort) && (
                                <TextField source="product_group_name" label="Group" />
                            )}
                            {has_attribute("branch_name", data, sort) && (
                                <TextField source="branch_name" label="Branch / Version" />
                            )}
                            {has_attribute("origin_service_name", data, sort) && (
                                <TextField source="origin_service_name" label="Service" />
                            )}
                            <BooleanField source="has_observations" label="Active observations" />
                        </Datagrid>
                    )}
                />
            </List>
        </Fragment>
    );
};

export default ComponentList;
