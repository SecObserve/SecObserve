import { Fragment } from "react";
import {
    BulkDeleteButton,
    Datagrid,
    DateField,
    List,
    TextField,
    TextInput,
    TopToolbar,
    WithListContext,
} from "react-admin";

import vex_documents from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { has_attribute } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import VEXDocumentImport from "./VEXDocumentImport";

const listFilters = [
    <TextInput source="document_id" label="Document ID" alwaysOn />,
    <TextInput source="author" alwaysOn />,
];

const ListActions = () => (
    <TopToolbar>
        <VEXDocumentImport />
    </TopToolbar>
);

const BulkActionButtons = () => (
    <Fragment>
        <BulkDeleteButton mutationMode="pessimistic" />
    </Fragment>
);

const VEXDocumentList = () => {
    return (
        <Fragment>
            <ListHeader icon={vex_documents.icon} title="Imported VEX documents" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "document_id", order: "ASC" }}
                actions={<ListActions />}
                disableSyncWithLocation={false}
                storeKey="vex_documents.list"
                empty={false}
            >
                <WithListContext
                    render={({ data, sort }) => (
                        <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={<BulkActionButtons />}>
                            <TextField source="type" />
                            <TextField source="document_id" label="Document ID" />
                            <TextField source="version" />
                            <DateField source="current_release_date" label="Current release" />
                            <TextField source="author" sx={{ wordBreak: "break-word" }} />
                            {has_attribute("role", data, sort) && <TextField source="role" />}
                        </Datagrid>
                    )}
                />
            </List>
        </Fragment>
    );
};

export default VEXDocumentList;
