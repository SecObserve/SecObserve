import { Fragment } from "react";
import { AutocompleteInput, Datagrid, List, TextField, TextInput } from "react-admin";

import parsers from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import ListHeader from "../../commons/layout/ListHeader";
import { getSettingListSize, getSettingRowsPerPage } from "../../commons/user_settings/functions";
import { PARSER_SOURCE_CHOICES, SCANNER_TYPE_CHOICES } from "../types";

const listFilters = [
    <TextInput source="name" alwaysOn />,
    <AutocompleteInput source="type" choices={SCANNER_TYPE_CHOICES} alwaysOn />,
    <AutocompleteInput source="source" choices={PARSER_SOURCE_CHOICES} alwaysOn />,
];

const ParserList = () => {
    return (
        <Fragment>
            <ListHeader icon={parsers.icon} title="Parsers" />
            <List
                perPage={getSettingRowsPerPage()}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "name", order: "ASC" }}
                actions={false}
                disableSyncWithLocation={false}
            >
                <Datagrid size={getSettingListSize()} rowClick={false} bulkActionButtons={false}>
                    <TextField source="name" />
                    <TextField source="type" />
                    <TextField source="source" />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default ParserList;
