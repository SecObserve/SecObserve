import { Fragment } from "react";
import { AutocompleteInput, Datagrid, List, ReferenceInput, TextField, TextInput } from "react-admin";

import audit_logs from ".";
import { getSettingListSize, getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { DateField } from "../../commons/custom_fields/DateField";
import { DateRangeFilter } from "../../commons/custom_fields/DateRangeFilter";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { getUserOptionText } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { AUDIT_LOG_ACTION_CHOICES } from "../types";

const listFilters = [
    <ProductReferenceInput key="product" alwaysOn />,
    <AutocompleteInput key="action" source="action" choices={AUDIT_LOG_ACTION_CHOICES} alwaysOn />,
    <ReferenceInput key="user" source="user" reference="users" sort={{ field: "full_name", order: "ASC" }} alwaysOn>
        <AutocompleteInputMedium optionText={getUserOptionText} />
    </ReferenceInput>,
    <TextInput key="target" source="target" alwaysOn />,
    <DateRangeFilter key="created" fields={[{ source: "created", label: "Created" }]} alwaysOn />,
];

const AuditLogList = () => {
    return (
        <Fragment>
            <ListHeader icon={audit_logs.icon} title="Audit Log" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "created", order: "DESC" }}
                actions={false}
                disableSyncWithLocation={false}
                storeKey="audit_logs.list"
                empty={false}
            >
                <Datagrid size={getSettingListSize()} rowClick={false} bulkActionButtons={false}>
                    <DateField source="created" showTime />
                    <TextField source="product_name" label="Product" emptyText="---" />
                    <TextField
                        source="authorization_group_name"
                        label="Authorization group"
                        emptyText="---"
                        sortable={false}
                    />
                    <TextField source="user_name" label="User" emptyText="---" />
                    <TextField source="action" />
                    <TextField source="target" sx={{ wordBreak: "break-word" }} />
                    <TextField source="old_value" label="Old value" emptyText="---" sortable={false} />
                    <TextField source="new_value" label="New value" emptyText="---" sortable={false} />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default AuditLogList;
