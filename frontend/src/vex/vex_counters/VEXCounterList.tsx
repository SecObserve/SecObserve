import { Fragment } from "react";
import { BulkDeleteButton, Datagrid, List, NumberField, NumberInput, TextField, TextInput } from "react-admin";

import vex_counters from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import ListHeader from "../../commons/layout/ListHeader";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";

const listFilters = [<TextInput source="document_id_prefix" alwaysOn />, <NumberInput source="year" alwaysOn />];

const BulkActionButtons = () => (
    <Fragment>
        <BulkDeleteButton mutationMode="pessimistic" />
    </Fragment>
);

const VEXCounterList = () => {
    return (
        <Fragment>
            <ListHeader icon={vex_counters.icon} title="VEX Counters" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "document_id_prefix", order: "ASC" }}
                actions={false}
                disableSyncWithLocation={false}
                storeKey="vex_counters.list"
            >
                <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={<BulkActionButtons />}>
                    <TextField source="document_id_prefix" label="Document ID prefix" />
                    <NumberField source="year" options={{ useGrouping: false }} />
                    <NumberField source="counter" sortable={false} />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default VEXCounterList;
