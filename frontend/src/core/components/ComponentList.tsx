import { Fragment } from "react";
import {
    AutocompleteInput,
    BooleanField,
    Datagrid,
    List,
    NullableBooleanInput,
    ReferenceInput,
    TextField,
    TextInput,
    WithListContext,
} from "react-admin";

import components from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { has_attribute } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium, AutocompleteInputWide } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import { PURL_TYPE_CHOICES } from "../types";

const listFilters = [
    <TextInput source="component_name_version" label="Component" alwaysOn />,
    <AutocompleteInput source="component_purl_type" label="Component type" choices={PURL_TYPE_CHOICES} alwaysOn />,
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
        alwaysOn
    >
        <AutocompleteInputWide label="Service" optionText="name_with_product" />
        <NullableBooleanInput source="has_observations" label="Open observations" alwaysOn />
    </ReferenceInput>,
];

const ComponentList = () => {
    return (
        <Fragment>
            <ListHeader icon={components.icon} title="Components" />
            <List
                perPage={25}
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
                            <BooleanField source="has_observations" label="Open observations" />
                        </Datagrid>
                    )}
                />
            </List>
        </Fragment>
    );
};

export default ComponentList;
