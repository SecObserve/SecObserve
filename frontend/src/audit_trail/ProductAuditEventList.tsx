import { Fragment } from "react";
import { ChipField, Datagrid, List, ReferenceInput, TextField, TextInput } from "react-admin";

import audit_trail from ".";
import { getSettingListSize, getSettingRowsPerPage } from "../access_control/users/functions";
import { CustomPagination } from "../commons/custom_fields/CustomPagination";
import { DateField } from "../commons/custom_fields/DateField";
import { DateRangeFilter } from "../commons/custom_fields/DateRangeFilter";
import { ProductReferenceInput } from "../commons/custom_fields/ProductReferenceInput";
import { getUserOptionText } from "../commons/functions";
import ListHeader from "../commons/layout/ListHeader";
import { AutocompleteInputMedium } from "../commons/layout/themes";
import { ChangesExpand, hasChanges } from "./ProductAuditEventEmbeddedList";
import { OBJECT_TYPE_CHOICES } from "./types";

const listFilters = [
    <ProductReferenceInput alwaysOn />,
    <TextInput source="product_name" label="Product name" alwaysOn />,
    <DateRangeFilter key="date" fields={[{ source: "created", label: "Created" }]} alwaysOn />,
    <AutocompleteInputMedium source="object_type" label="Object type" choices={OBJECT_TYPE_CHOICES} alwaysOn />,
    <TextInput source="q" label="Name" alwaysOn />,
    <ReferenceInput
        source="user"
        reference="users"
        queryOptions={{ meta: { api_resource: "user_names" } }}
        sort={{ field: "full_name", order: "ASC" }}
        alwaysOn
    >
        <AutocompleteInputMedium optionText={getUserOptionText} />
    </ReferenceInput>,
];

const ProductAuditEventList = () => {
    return (
        <Fragment>
            <ListHeader icon={audit_trail.icon} title="Audit Trail" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "created", order: "DESC" }}
                disableSyncWithLocation={false}
                storeKey="product_audit_events.list"
                actions={false}
            >
                <Datagrid
                    size={getSettingListSize()}
                    bulkActionButtons={false}
                    rowClick="expand"
                    expand={<ChangesExpand />}
                    isRowExpandable={hasChanges}
                    expandSingle
                >
                    <TextField source="product_name" label="Product" />
                    <DateField source="created" showTime />
                    <ChipField source="object_type" label="Object type" />
                    <TextField source="object_name" label="Name" />
                    <TextField source="action" />
                    <TextField source="user_full_name" label="User" />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default ProductAuditEventList;
