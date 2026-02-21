import { Fragment } from "react";
import {
    ChipField,
    Datagrid,
    FunctionField,
    List,
    NumberField,
    ReferenceManyField,
    SingleFieldList,
    TextField,
    TextInput,
    TopToolbar,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { humanReadableDate } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { getSettingListSize } from "../../commons/user_settings/functions";
import openvex from "../../vex/openvex";
import { OpenVEX } from "../../vex/types";
import OpenVEXCreate from "./OpenVEXCreate";

const listFilters = [
    <ProductReferenceInput alwaysOn />,
    <TextInput source="vulnerability_names__name" label="Vulnerability" alwaysOn />,
];

const ListActions = () => (
    <TopToolbar>
        <OpenVEXCreate />
    </TopToolbar>
);

const OpenVEXList = () => {
    return (
        <Fragment>
            <ListHeader icon={openvex.icon} title="Exported OpenVEX documents" />
            <List
                perPage={25}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "timestamp", order: "DESC" }}
                actions={<ListActions />}
                disableSyncWithLocation={false}
                storeKey="openvex.list"
                empty={false}
            >
                <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={false}>
                    <TextField source="product_data.name" label="Product" />
                    <ReferenceManyField
                        reference="vex/openvex_vulnerabilities"
                        target="openvex"
                        label="Vulnerabilities"
                    >
                        <SingleFieldList linkType={false}>
                            <ChipField source="name" />
                        </SingleFieldList>
                    </ReferenceManyField>
                    <ReferenceManyField reference="vex/openvex_branches" target="openvex" label="Branches / Versions">
                        <SingleFieldList linkType={false}>
                            <ChipField source="name" />
                        </SingleFieldList>
                    </ReferenceManyField>
                    <TextField source="id_namespace" label="ID namespace" />
                    <TextField source="document_id_prefix" label="ID prefix" sx={{ wordBreak: "break-word" }} />
                    <TextField source="document_base_id" label="Base ID" />
                    <NumberField source="version" label="Version" />
                    <TextField source="author" label="Author" sx={{ wordBreak: "break-word" }} />
                    <FunctionField<OpenVEX>
                        label="Created"
                        sortBy="timestamp"
                        render={(record) => (record ? humanReadableDate(record.timestamp) : "")}
                    />
                    <FunctionField<OpenVEX>
                        label="Updated"
                        sortBy="last_updated"
                        render={(record) => (record ? humanReadableDate(record.last_updated) : "")}
                    />
                    <TextField source="user_full_name" label="User" />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default OpenVEXList;
