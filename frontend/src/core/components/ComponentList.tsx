import { Fragment } from "react";
import { BooleanField, Datagrid, List, NullableBooleanInput, TextField, TextInput } from "react-admin";

import components from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { COMPONENT_TYPE_CHOICES } from "../../licenses/types";
import { PURL_TYPE_CHOICES } from "../types";

const listFilters = [
    <TextInput source="name_version" label="Component" alwaysOn />,
    <AutocompleteInputMedium source="purl_type" label="Ecosystem" choices={PURL_TYPE_CHOICES} alwaysOn />,
    <AutocompleteInputMedium source="type" label="Type" choices={COMPONENT_TYPE_CHOICES} alwaysOn />,
    <NullableBooleanInput source="has_observations" label="Active observations" alwaysOn />,
    <NullableBooleanInput source="has_licenses" label="Licenses" alwaysOn />,
];

const ComponentList = () => {
    return (
        <Fragment>
            <ListHeader icon={components.icon} title="Components" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "name_version_type", order: "ASC" }}
                disableSyncWithLocation={false}
                actions={false}
                storeKey="components.list"
            >
                <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={false}>
                    <TextField source="name_version_type" label="Component" />
                    <TextField source="type" label="Type" />
                    <BooleanField source="has_observations" label="Active observations" sortable={false} />
                    <BooleanField source="has_licenses" label="Licenses" sortable={false} />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default ComponentList;
